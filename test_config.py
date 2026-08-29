from dotenv import load_dotenv
import os 

#  加载 .env 文件
load_dotenv()

# 读取环境变量
api_key = os.getenv("DEEPSEEK_API_KEY")
base_url = os.getenv("DEEPSEEK_BASE_URL")

# 验证
if api_key:
    print(f"✅ API Key: {api_key[:10]}...{api_key[-4:]}")
else:
    print("❌ 未找到API Key")
    
if base_url:
    print(f"✅ Base URL: {base_url}")
else:
    print("❌ 未找到Base URL")