"""测试重试机制的脚本"""
import asyncio
from explainer import CodeExplainer

async def test():
    explainer = CodeExplainer()
    
    # 测试代码
    code = """
def hello():
    print("Hello World")
"""
    
    try:
        await explainer.explain_code(code, "test.py")
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    asyncio.run(test())
