import os
import requests
import zipfile
import shutil
import glob
import time

def main():
    cookies = {
        'sessionid': 'u5q0yb5v2gjsdf62cmv2jlvne2qgysyd',
        'csrftoken': 'hYIdTPE2bv49fv2nUMria6xUwXQRb3Po'
    }
    headers = {
        'Referer': 'https://cvat.note.transformerlabs.ai/',
        'X-CSRFToken': 'hYIdTPE2bv49fv2nUMria6xUwXQRb3Po',
        'Content-Type': 'application/json'
    }
    
    # Init export
    url = "https://cvat.note.transformerlabs.ai/api/jobs/5931/dataset/export?save_images=True&format=Sly%20Point%20Cloud%20Format%201.0"
    print(f"Initiating export: {url}")
    
    resp = requests.post(url, cookies=cookies, headers=headers, json={"save_images": True, "format": "Sly Point Cloud Format 1.0"})
    if resp.status_code not in (200, 201, 202):
        print("Failed to start export:", resp.status_code, resp.text)
        return
        
    rq_id = resp.json().get("rq_id")
    print(f"Export started, rq_id: {rq_id}")
    
    # Polling
    status_url = f"https://cvat.note.transformerlabs.ai/api/requests/{rq_id}"
    while True:
        time.sleep(3)
        res = requests.get(status_url, cookies=cookies, headers=headers)
        data = res.json()
        status = data.get("status")
        print(f"Polling... Status: {status}")
        if status == "finished":
            result_url = data.get("result_url")
            print(f"Finished! Download URL: {result_url}")
            break
        elif status == "failed":
            print("Export failed:", data)
            return
            
    # Download
    print("Downloading file...")
    download_url = "https://cvat.note.transformerlabs.ai" + result_url if result_url.startswith("/") else result_url
    dl_resp = requests.get(download_url, cookies=cookies, headers=headers)
    
    if dl_resp.status_code == 200:
        with open('dataset.zip', 'wb') as f:
            f.write(dl_resp.content)
        print("Downloaded dataset.zip")
    else:
        print("Download failed:", dl_resp.status_code)
        return

    # Clear old pointcloud
    shutil.rmtree("pointcloud", ignore_errors=True)
    os.makedirs("pointcloud", exist_ok=True)
    
    print("Extracting...")
    with zipfile.ZipFile('dataset.zip', 'r') as zip_ref:
        zip_ref.extractall("temp_dataset")
        
    pcd_files = glob.glob("temp_dataset/**/*.pcd", recursive=True)
    for f in pcd_files:
        shutil.move(f, os.path.join("pointcloud", os.path.basename(f)))
        
    print(f"Moved {len(pcd_files)} PCD files to pointcloud/")
    shutil.rmtree("temp_dataset", ignore_errors=True)
    os.remove("dataset.zip")

if __name__ == '__main__':
    main()
