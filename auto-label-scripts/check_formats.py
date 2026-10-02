from cvat_sdk import make_client

HOST = "https://cvat.note.transformerlabs.ai"
USERNAME = "2A202602208"
PASSWORD = "l3CjOiD-HQxcjgu8"

try:
    with make_client(host=HOST, credentials=(USERNAME, PASSWORD)) as client:
        print("[OK] Ket noi CVAT thanh cong!")
        
        # In ra cac dinh dang export ho tro
        formats = client.server_api.list_annotation_formats()[0]
        
        print("Cac dinh dang ho tro Dataset (co the chua PCD):")
        for f in formats.results:
            if '3D' in f.name:
                print(f" - {f.name}")
                
except Exception as e:
    print(f"Error: {e}")
