from cvat_sdk import make_client
import json

HOST = "https://cvat.note.transformerlabs.ai"
USERNAME = "2A202602208"
PASSWORD = "l3CjOiD-HQxcjgu8"
JOB_ID = 3929

try:
    with make_client(host=HOST, credentials=(USERNAME, PASSWORD)) as client:
        print("[OK] Ket noi CVAT thanh cong!")
        
        job = client.jobs.retrieve(JOB_ID)
        print(f"Job frames: {job.start_frame} -> {job.stop_frame} ({job.stop_frame - job.start_frame + 1} frames)")
        
        # Lay labels qua job API
        labels_api = client.api_client.labels_api
        labels_data, _ = labels_api.list(job_id=JOB_ID)
        
        print(f"\n=== LABELS trong Job {JOB_ID} ===")
        label_map = {}
        for lbl in labels_data.results:
            label_map[lbl.id] = lbl.name
            attrs_info = [f"{a.name}({a.input_type})" for a in (lbl.attributes or [])]
            print(f"  ID={lbl.id} | Name={lbl.name} | Type={lbl.type} | Attrs={attrs_info}")
        
        print(f"\nTotal labels: {len(label_map)}")
        print(f"Label map: {json.dumps(label_map, indent=2)}")

except Exception as e:
    import traceback
    print(f"[ERROR] {type(e).__name__}: {e}")
    traceback.print_exc()
