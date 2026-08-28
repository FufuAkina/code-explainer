# test_stress.py
import asyncio
from explainer import CodeExplainer

async def test_large_file():
    """测试大文件"""
    # 生成5000行代码
    large_code = "\n".join([f"def func_{i}(): pass" for i in range(5000)])
    
    explainer = CodeExplainer()
    
    try:
        await explainer.explain_code(large_code, "large.py")
        print("✅ 大文件测试通过")
    except Exception as e:
        print(f"❌ 大文件测试失败: {e}")

async def test_unicode():
    """测试 Unicode 字符"""
    code_with_unicode = """
def greet():
    print("你好 🌍")
    print("こんにちは")
    """
    
    explainer = CodeExplainer()
    
    try:
        await explainer.explain_code(code_with_unicode, "unicode.py")
        print("✅ Unicode 测试通过")
    except Exception as e:
        print(f"❌ Unicode 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_large_file())
    asyncio.run(test_unicode())
