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

# Test both environment variable keys
token1 = os.getenv("QWEN_API_KEY")
token2 = os.getenv("ALIBABA_CLOUD_MODEL_API_KEY")

token = token1 or token2
if not token:
    print("Neither QWEN_API_KEY nor ALIBABA_CLOUD_MODEL_API_KEY found in .env!")
    exit(1)

print(f"API Key found: {token[:12]}...{token[-4:]}")

# We will test two international endpoints
endpoints = [
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
    "https://dashscope.ap-southeast-1.aliyuncs.com/compatible-mode/v1/chat/completions"
]

for url in endpoints:
    print(f"\n--- Testing Endpoint: {url} ---")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "qwen-plus",
        "messages": [
            {"role": "user", "content": "Hello! Answer in 5 words."}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        print(f"HTTP Status Code: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS connected successfully!")
            print(f"Response: {response.json()['choices'][0]['message']['content']}")
        else:
            print(f"FAILED: Status: {response.status_code}, Msg: {response.text}")
    except Exception as e:
        print(f"Error occurred: {str(e)}")
