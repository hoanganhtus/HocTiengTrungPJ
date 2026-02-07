import requests
import json

url = "http://127.0.0.1:8000/translator/chat/"
payload = {
    "message": "Tôi là kỹ sư phần mềm, em trai tôi học thương mại điện tử"
}

try:
    print(f"Dang gui yeu cau den: {url}...")
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        print("\n--- KET QUA THANH CONG ---")
        data = response.json()
        print(data['reply'])
    else:
        print(f"\n--- LOI ({response.status_code}) ---")
        print(response.text)
        
except Exception as e:
    print(f"Loi ket noi: {e}")