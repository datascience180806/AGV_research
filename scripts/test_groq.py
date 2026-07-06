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
token = os.getenv("GROQ_API_KEY")

if not token:
    print("GROQ_API_KEY not found in .env file!")
    exit(1)

print(f"GROQ_API_KEY found: {token[:8]}...{token[-4:]}")

url = "https://api.groq.com/openai/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
payload = {
    "model": "openai/gpt-oss-20b",
    "messages": [
        {"role": "user", "content": "Hi, answer in 5 words."}
    ]
}

try:
    print("Sending test request to Groq API...")
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    print(f"HTTP Status Code: {response.status_code}")
    if response.status_code == 200:
        print("SUCCESS: Groq API key is working correctly!")
        print(f"Response: {response.json()['choices'][0]['message']['content']}")
    else:
        print(f"FAILED: Groq is not working. Status: {response.status_code}, Msg: {response.text}")
except Exception as e:
    print(f"Error occurred during API request: {str(e)}")
