import os
import requests
from dotenv import load_dotenv

# Set console output encoding to UTF-8 to prevent cp1252 errors on Windows
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

dotenv_path = os.path.join(os.getcwd(), ".env")
print("Loading .env from:", dotenv_path)
load_dotenv(dotenv_path=dotenv_path, override=True)
token = os.getenv("HF_TOKEN")

if not token:
    print("HF_TOKEN not found in .env file!")
    exit(1)

url = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-Coder-1.5B-Instruct"
headers = {"Authorization": f"Bearer {token}"}
payload = {"inputs": "Hi, who are you?"}

# Danh sách các proxy để thử nghiệm
# 127.0.0.1:40000 là cổng mặc định của Cloudflare WARP ở chế độ Local Proxy
proxy_options = [
    {"name": "Không dùng Proxy (Mặc định)", "proxies": None},
    {"name": "SOCKS5 Proxy (Cloudflare WARP - socks5h://127.0.0.1:40000)", 
     "proxies": {"http": "socks5h://127.0.0.1:40000", "https": "socks5h://127.0.0.1:40000"}},
    {"name": "HTTP Proxy (Cloudflare WARP - http://127.0.0.1:40000)", 
     "proxies": {"http": "http://127.0.0.1:40000", "https": "http://127.0.0.1:40000"}},
    {"name": "SOCKS5 Proxy (Cổng 10808 phổ biến)", 
     "proxies": {"http": "socks5h://127.0.0.1:10808", "https": "socks5h://127.0.0.1:10808"}},
    {"name": "HTTP Proxy (Cổng 7890 phổ biến)", 
     "proxies": {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}}
]

print("Bắt đầu chẩn đoán kết nối tới Hugging Face...")

for opt in proxy_options:
    print(f"\n--- Thử nghiệm: {opt['name']} ---")
    try:
        response = requests.post(url, headers=headers, json=payload, proxies=opt["proxies"], timeout=10)
        print(f"HTTP Status Code: {response.status_code}")
        if response.status_code == 200:
            print("=> SUCCESS: Kết nối THÀNH CÔNG!")
            print(f"Phản hồi từ model: {response.json()}")
            print(f"\n[KHUYÊN DÙNG] Hãy sử dụng cấu hình proxy này!")
            # Kết thúc sớm nếu thành công
            break
        else:
            print(f"=> Thất bại (Mã lỗi HTTP: {response.status_code})")
    except Exception as e:
        print(f"=> Lỗi kết nối: {str(e)[:150]}...")
