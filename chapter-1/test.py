import base64
import requests

url = "http://localhost:8000/detect"
file_path = "sample.jpg"
output_path = "output.jpg"

response_type = "url"   # "base64" 또는 "url"

with open(file_path, "rb") as f:
    response = requests.post(
        url,
        data={
            "message": "Test message",
            "responseType": response_type
        },
        files={"file": f}
    )

if response.status_code != 200:
    print("Request failed:", response.status_code)
    print(response.text)
    exit()

data = response.json()
print("message:", data["message"])

if response_type == "url":    # URL로 이미지 다운로드
    print("image url:", data["url"])
elif response_type == "base64": # Base64로 이미지 다운로드
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(data["image"]))
    print("saved:", output_path)