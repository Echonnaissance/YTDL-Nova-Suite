"""
Cleanup script: delete failed downloads with format 'm4a'
Usage: backend\\venv\\Scripts\\python.exe scripts\\cleanup_failed_m4a.py
"""
import requests

API = "http://127.0.0.1:8000/api"


def main():
    print("Fetching failed downloads...")
    r = requests.get(f"{API}/downloads",
                     params={"status": "failed", "limit": 1000})
    r.raise_for_status()
    items = r.json()
    to_delete = [i for i in items if i.get("format") == "m4a"]
    print(f"Found {len(to_delete)} failed 'm4a' entries to delete.")
    deleted = 0
    for item in to_delete:
        did = item.get("id")
        try:
            dr = requests.delete(f"{API}/downloads/{did}")
            if dr.status_code in (200, 204, 202, 205):
                deleted += 1
                print(f"Deleted {did}")
            elif dr.status_code == 404:
                print(f"Not found {did}")
            else:
                print(f"Failed to delete {did}: {dr.status_code} {dr.text}")
        except Exception as e:
            print(f"Error deleting {did}: {e}")
    print(f"Done. Deleted {deleted} entries.")


if __name__ == '__main__':
    main()
