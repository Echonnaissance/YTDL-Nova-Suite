# To start the backend in a separate terminal on Windows, run:
# cmd /c start "UMD - Backend" /D "C:\Users\Anthony Ferraro\coding-projects\active-projects\Univeral Media Download Converter\backend" cmd /k "venv\Scripts\activate && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

import requests

data = {
    "url": "",
    "download_type": "audio",
    "format": "m4a",
    "quality": "best",
    "embed_thumbnail": True
}

r = requests.post('http://127.0.0.1:8000/api/downloads/',
                  json=data, timeout=60)
print(r.status_code)
print(r.text)
