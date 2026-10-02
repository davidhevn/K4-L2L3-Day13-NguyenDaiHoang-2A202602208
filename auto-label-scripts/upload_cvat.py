import json
from cvat_sdk import make_client
from cvat_sdk.models import LabeledDataRequest, LabeledShapeRequest, PatchedLabeledDataRequest

HOST = "https://cvat.note.transformerlabs.ai"
USERNAME = "2A202602208"
PASSWORD = "l3CjOiD-HQxcjgu8"
JOB_ID = 5931
JSON_FILE = "cvat_annotations/cvat_3d_annotations.json"

def main():
    # 1. Doc file json
    try:
        with open(JSON_FILE, 'r') as f:
            data = json.load(f)
        print(f"[+] Da doc {len(data)} objects tu {JSON_FILE}")
    except Exception as e:
        print(f"[!] Khong the doc {JSON_FILE}: {e}")
        return

    # 2. Ket noi CVAT
    try:
        with make_client(host=HOST, credentials=(USERNAME, PASSWORD)) as client:
            job = client.jobs.retrieve(JOB_ID)
            
            # Lay label mapping cua job
            labels_api = client.api_client.labels_api
            labels_data, _ = labels_api.list(job_id=JOB_ID)
            label_map = {lbl.name: lbl.id for lbl in labels_data.results}
            
            shapes = []
            
            # 3. Parse data
            for obj in data:
                label_name = obj.get('label')
                label_id = label_map.get(label_name)
                
                if not label_id:
                    print(f"[-] Bo qua label {label_name} vi khong co tren CVAT.")
                    continue
                
                # Format 3D Cuboid tren CVAT SDK
                # Elements cho cuboid: position (3), rotation (3), dimension (3) -> total 9 floats
                # CVAT points array for cuboid: [pos_x, pos_y, pos_z, rot_x, rot_y, rot_z, dim_x, dim_y, dim_z]
                
                pos = obj['position']
                rot = obj['rotation']
                dim = obj['dimension']
                
                # CVAT API requires exactly 16 values in the points array for shape type 'cuboid'
                cuboid_elements = [
                    pos['x'], pos['y'], pos['z'],
                    rot['x'], rot['y'], rot['z'],
                    dim['x'], dim['y'], dim['z'],
                    0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                ]
                
                shape = LabeledShapeRequest(
                    frame=int(obj['frame']),
                    label_id=label_id,
                    type='cuboid',
                    points=cuboid_elements,
                    occluded=False,
                    outside=False,
                    z_order=0
                )
                shapes.append(shape)
                
            if not shapes:
                print("[!] Khong co objects nao hop le de upload.")
                return
                
            print(f"[+] Dang upload {len(shapes)} 3D cuboids len Job {JOB_ID}...")
            
            # 4. Upload annotations
            # Ghi de (PUT) hoac Them moi (PATCH)
            # Dung PATCH de them vao hoac tao moi
            labeled_data = PatchedLabeledDataRequest(
                shapes=shapes,
                tracks=[],
                tags=[]
            )
            
            client.jobs.api.partial_update_annotations(action="create", id=JOB_ID, patched_labeled_data_request=labeled_data)
            print("[OK] Thanh cong! Hay F5 lai trang CVAT.")
            
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == '__main__':
    main()
