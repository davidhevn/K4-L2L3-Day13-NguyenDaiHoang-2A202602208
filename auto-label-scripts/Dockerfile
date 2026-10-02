FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-devel

# Cai dat thu vien he thong va ngan no hoi timezone
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y git libgl1-mesa-glx libglib2.0-0 wget ninja-build tzdata

# Cai thu vien spconv cho CUDA 11.8
RUN pip install spconv-cu118

# Cai Open3D va cac thu vien phu tro
RUN pip install open3d tensorboardX easydict pyyaml scikit-image tqdm SharedArray six cvat-sdk opencv-python-headless

# Clone va cai dat OpenPCDet
RUN git clone https://github.com/open-mmlab/OpenPCDet.git /opt/OpenPCDet
WORKDIR /opt/OpenPCDet

# CHI CHO PHEP CHAY 2 LUONG DE KHONG BI TRAN RAM
ENV MAX_JOBS=2
ENV TORCH_CUDA_ARCH_LIST="8.9"
RUN python setup.py develop

# Cai dat them cac thu vien phu thuoc phat sinh
RUN pip install "numpy==1.23.5" av2 "kornia==0.6.8" nuscenes-devkit

# Chuyen ve thu muc lam viec
WORKDIR /workspace

# Lenh mac dinh khi chay container
CMD ["sh", "-c", "python auto_annotate.py"]
