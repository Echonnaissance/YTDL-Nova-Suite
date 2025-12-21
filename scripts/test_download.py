import time
import requests
import sys

API_BASE = "http://127.0.0.1:8000/api"
post_url = f"{API_BASE}/downloads"

payload = {
    "url": "https://file-examples.com/wp-content/uploads/2017/04/file_example_MP4_480_1_5MG.mp4",
    "download_type": "video",
    "format": "mp4"
}

print("Posting test download request...")
try:
    r = requests.post(post_url, json=payload, timeout=30)
except Exception as e:
    print("POST request failed:", e)
    sys.exit(1)

print('POST status:', r.status_code)
try:
    print(r.json())
except Exception:
    print(r.text)

if r.status_code not in (200, 201):
    print("POST failed; aborting.")
    sys.exit(2)

data = r.json()
if isinstance(data, list):
    download_id = data[0].get("id")
else:
    download_id = data.get("id")

if not download_id:
    print("Could not determine download id from response; aborting.")
    sys.exit(3)

print(f"Queued download id: {download_id}")

# Poll status
get_url = f"{API_BASE}/downloads/{download_id}"
start = time.time()
timeout = 300  # seconds
interval = 3
while True:
    try:
        r = requests.get(get_url, timeout=10)
    except Exception as e:
        print("Error polling status:", e)
        time.sleep(interval)
        continue

    if r.status_code == 200:
        info = r.json()
        status = info.get("status")
        progress = info.get("progress")
        print(f"Status: {status}  progress: {progress}")
        if status and status.lower() in ("completed", "failed", "cancelled"):
            print("Final status:", status)
            print("Download record:", info)
            break
    else:
        print("Poll returned", r.status_code, r.text)

    if time.time() - start > timeout:
        print("Timeout waiting for download to finish")
        break

    time.sleep(interval)

print("Test finished.")
