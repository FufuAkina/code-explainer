import os
from dotenv import load_dotenv
import requests

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")
base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

print(f"API Key: {api_key[:10]}...{api_key[-4:]}")
print(f"Base URL: {base_url}")

# 测试API连接
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# 尝试不同的端点
endpoints = [
    f"{base_url}/chat/completions",
    f"{base_url}/v1/chat/completions",
    "https://api.deepseek.com/chat/completions",
    "https://api.deepseek.com/v1/chat/completions"
]

for endpoint in endpoints:
    print(f"\n测试端点: {endpoint}")
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10
            },
            timeout=10
        )
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ 成功！正确的端点是: {endpoint}")
            break
        else:
            print(f"响应: {response.text[:200]}")
    except Exception as e:
        print(f"❌ 错误: {e}")