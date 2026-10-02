import os
import glob
import json
import numpy as np
import torch
import open3d as o3d
from pcdet.config import cfg, cfg_from_yaml_file
from pcdet.models import build_network, load_data_to_gpu
from pcdet.datasets import DatasetTemplate
from pcdet.utils import common_utils

class CustomPCDDataset(DatasetTemplate):
    def __init__(self, dataset_cfg, class_names, training=True, root_path=None, logger=None, ext='.pcd'):
        super().__init__(dataset_cfg=dataset_cfg, class_names=class_names, training=training, root_path=root_path, logger=logger)
        self.root_path = root_path
        self.ext = ext
        self.sample_file_list = glob.glob(os.path.join(self.root_path, f'*{self.ext}'))
        # Ensure files are sorted to keep frame indices consistent
        self.sample_file_list.sort()
        
    def __len__(self):
        return len(self.sample_file_list)
    
    def __getitem__(self, index):
        file_path = self.sample_file_list[index]
        
        # Load .pcd file using Open3D
        pcd = o3d.io.read_point_cloud(file_path)
        points = np.asarray(pcd.points)
        
        # nuScenes models in OpenPCDet expect [N, 5] with (x, y, z, intensity, timestamp). 
        # Pad with zeros to match 5 features.
        if points.shape[1] == 3:
            padding = np.zeros((points.shape[0], 2))
            points = np.hstack([points, padding])
        elif points.shape[1] == 4:
            padding = np.zeros((points.shape[0], 1))
            points = np.hstack([points, padding])
            
        points = points.astype(np.float32)
        
        input_dict = {
            'points': points,
            'frame_id': os.path.basename(file_path).split('.')[0],
            'frame_index': int(os.path.basename(file_path).split('.')[0]) # Sử dụng đúng frame id từ tên file thay vì index 0,1,2
        }
        
        data_dict = self.prepare_data(data_dict=input_dict)
        return data_dict

def main():
    # 1. Tích hợp File Config YAML
    os.chdir('/opt/OpenPCDet/tools')
    cfg_file = 'cfgs/nuscenes_models/cbgs_pp_multihead.yaml'
    ckpt_file = '/workspace/cbgs_pp_multihead.pth' 
    data_path = '/workspace/pointcloud' 
    output_dir = '/workspace/cvat_annotations'
    confidence_threshold = 0.05
    
    os.makedirs(output_dir, exist_ok=True)
    
    logger = common_utils.create_logger()
    
    # Load config từ OpenPCDet
    if os.path.exists(cfg_file):
        cfg_from_yaml_file(cfg_file, cfg)
    else:
        logger.error(f"Không tìm thấy file config {cfg_file}. Vui lòng chạy script tại thư mục gốc OpenPCDet.")
        return
    
    # 2. Class Mapping chuẩn nuScenes
    # nuScenes class list theo đúng document (10 classes)
    NUSCENES_CLASSES = {
        1: 'car',
        2: 'truck',
        3: 'construction_vehicle',
        4: 'bus',
        5: 'trailer',
        6: 'barrier',
        7: 'motorcycle',
        8: 'bicycle',
        9: 'pedestrian',
        10: 'traffic_cone'
    }
    class_names = list(NUSCENES_CLASSES.values())

    dataset = CustomPCDDataset(
        dataset_cfg=cfg.DATA_CONFIG, class_names=class_names, training=False, root_path=data_path, logger=logger
    )

    logger.info(f'Total point cloud files: {len(dataset)}')

    # Khởi tạo model 
    model = build_network(model_cfg=cfg.MODEL, num_class=len(class_names), dataset=dataset)
    model.load_params_from_file(filename=ckpt_file, logger=logger, to_cpu=True)
    model.cuda()
    model.eval()

    all_cvat_annotations = []

    # Inference 
    with torch.no_grad():
        for idx in range(len(dataset)):
            data_dict = dataset[idx]
            
            # Lưu lại thông tin frame
            frame_id = data_dict['frame_id']
            frame_index = data_dict['frame_index']
            
            # Batch size = 1
            batch_dict = dataset.collate_batch([data_dict])
            load_data_to_gpu(batch_dict)
            
            pred_dicts, _ = model.forward(batch_dict)
            
            # Giải phóng GPU Memory - Bảo vệ VRAM 6GB
            torch.cuda.empty_cache()
            
            pred_dict = pred_dicts[0]
            
            # Áp dụng Center-Distance NMS để loại bỏ box trùng
            centers = pred_dict['pred_boxes'][:, :3].cpu().numpy()
            scores = pred_dict['pred_scores'].cpu().numpy()
            
            keep_indices = []
            sorted_indices = np.argsort(-scores)
            
            for idx in sorted_indices:
                if scores[idx] < confidence_threshold:
                    continue
                    
                center = centers[idx]
                is_overlap = False
                for keep_idx in keep_indices:
                    keep_center = centers[keep_idx]
                    dist = np.linalg.norm(center - keep_center)
                    if dist < 1.0: # Khoảng cách < 1m -> trùng
                        is_overlap = True
                        break
                
                if not is_overlap:
                    keep_indices.append(idx)
                    
            pred_boxes = pred_dict['pred_boxes'][keep_indices].cpu().numpy()
            pred_scores = pred_dict['pred_scores'][keep_indices].cpu().numpy()
            pred_labels = pred_dict['pred_labels'][keep_indices].cpu().numpy()
            
            for i in range(len(pred_scores)):
                
                # 3. Chuẩn hóa hệ tọa độ (Coordinate System)
                # Lidar OpenPCDet format for NuScenes: (x, y, z, dx, dy, dz, heading, vx, vy)
                x, y, z, dx, dy, dz, heading = pred_boxes[i][:7]

                
                label_id = pred_labels[i]
                class_name = NUSCENES_CLASSES.get(label_id, 'unknown')
                
                # Chuyen doi sang class cua Job 5931
                cvat_class_map = {
                    'car': 'vehicles',
                    'truck': 'vehicles',
                    'bus': 'vehicles',
                    'trailer': 'vehicles',
                    'construction_vehicle': 'vehicles',
                    'pedestrian': 'pedestrian',
                    'motorcycle': 'two-wheels',
                    'bicycle': 'two-wheels',
                    'barrier': 'Obstacle',
                    'traffic_cone': 'Obstacle'
                }
                cvat_class_name = cvat_class_map.get(class_name, class_name)
                
                # Yaw: CVAT yêu cầu góc Euler. 
                # Lưu ý: Tuỳ vào góc nhìn mặc định trên CVAT (phụ thuộc vào hệ trục của file PCD),
                # bạn có thể cần bù thêm pi/2. 
                yaw = float(heading)
                # yaw = float(heading) - np.pi / 2 # Mở comment dòng này nếu box trong CVAT bị xoay dọc ngang 90 độ
                
                # 4. Format JSON CVAT 1.1 3D
                cvat_obj = {
                    "frame": int(frame_index),
                    "label": cvat_class_name,
                    "position": {
                        "x": float(x), 
                        "y": float(y), 
                        "z": float(z)
                    },
                    "rotation": {
                        "x": 0.0, # pitch
                        "y": 0.0, # roll
                        "z": yaw  # yaw
                    }, 
                    "dimension": {
                        "x": float(dx), 
                        "y": float(dy), 
                        "z": float(dz)
                    },
                    "attributes": {
                        "confidence": float(pred_scores[i])
                    }
                }
                all_cvat_annotations.append(cvat_obj)

            logger.info(f'Processed {frame_id} (Frame {frame_index})')

    # Lưu toàn bộ annotations theo format CVAT (thường chứa mảng các object hoặc tracks)
    # File tổng hợp json 
    final_output_file = os.path.join(output_dir, 'cvat_3d_annotations.json')
    with open(final_output_file, 'w') as f:
        json.dump(all_cvat_annotations, f, indent=4)
        
    logger.info(f'Xong! Toàn bộ annotations được lưu tại {final_output_file}')

if __name__ == '__main__':
    main()
