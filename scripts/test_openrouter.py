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
token = os.getenv("OPENROUTER_API_KEY")

if not token:
    print("OPENROUTER_API_KEY not found in .env file!")
    exit(1)

print(f"OPENROUTER_API_KEY found: {token[:12]}...{token[-4:]}")

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
payload = {
    "model": "meta-llama/llama-3.2-3b-instruct:free",
    "messages": [
        {"role": "user", "content": "Hi, answer in 5 words."}
    ]
}

try:
    print("Sending test request to OpenRouter API...")
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    print(f"HTTP Status Code: {response.status_code}")
    if response.status_code == 200:
        print("SUCCESS: OpenRouter API key is working correctly!")
        print(f"Response: {response.json()['choices'][0]['message']['content']}")
    else:
        print(f"FAILED: OpenRouter is not working. Status: {response.status_code}, Msg: {response.text}")
except Exception as e:
    print(f"Error occurred during API request: {str(e)}")
