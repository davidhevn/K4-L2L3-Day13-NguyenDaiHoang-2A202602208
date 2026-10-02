from cvat_sdk import make_client
import os
import zipfile

HOST = "https://cvat.note.transformerlabs.ai"
USERNAME = "2A202602208"
PASSWORD = "l3CjOiD-HQxcjgu8"
JOB_ID = 3929

try:
    with make_client(host=HOST, credentials=(USERNAME, PASSWORD)) as client:
        print("[+] Dang ket noi CVAT...")
        job = client.jobs.retrieve(JOB_ID)
        
        # Format name phai khop chinh xac voi ten tren CVAT (Datumaro 3D 1.0)
        export_format = "Datumaro 3D 1.0"
        output_path = "dataset_job_3929.zip"
        
        print(f"[+] Dang yeu cau CVAT export data format '{export_format}'...")
        # export_dataset se tra ve data duoi dang zip
        job.export_dataset(format_name=export_format, filename=output_path, include_images=True)
        
        print(f"[OK] Da tai ve file: {output_path}")
        
        # Giai nen luon vao thu muc pointcloud
        print("[+] Dang giai nen file zip...")
        with zipfile.ZipFile(output_path, 'r') as zip_ref:
            zip_ref.extractall("job_3929_extracted")
            
        print("[OK] Hoan tat! Kiem tra thu muc job_3929_extracted")

except Exception as e:
    import traceback
    print(f"[ERROR] {type(e).__name__}: {e}")
    traceback.print_exc()
