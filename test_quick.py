"""快速测试错误处理"""
import sys

# 测试1：检查异常类定义位置
print("[测试1] 检查异常类定义...")
try:
    from explainer import RetryableError, NonRetryableError
    print("✅ 异常类可以导入")
except ImportError as e:
    print(f"❌ 异常类导入失败: {e}")
    sys.exit(1)

# 测试2：检查错误处理逻辑顺序
print("\n[测试2] 检查代码逻辑顺序...")
with open("explainer.py", "r", encoding="utf-8") as f:
    content = f.read()
    
    # 找到错误检查的位置
    error_check_pos = content.find('if chunk.get("type") == "error"')
    choices_check_pos = content.find('if "choices" in chunk')
    
    if error_check_pos < choices_check_pos and error_check_pos > 0:
        print("✅ 错误事件处理在 choices 检查之前")
    else:
        print("❌ 错误事件处理位置不对")

# 测试3：检查是否使用了正确的异常类型
print("\n[测试3] 检查异常类型使用...")
if 'raise RetryableError(f"服务器过载' in content:
    print("✅ overloaded_error 使用 RetryableError")
else:
    print("❌ overloaded_error 应该使用 RetryableError")

if 'raise RetryableError(f"速率限制' in content:
    print("✅ rate_limit_error 使用 RetryableError")
else:
    print("❌ rate_limit_error 应该使用 RetryableError")

print("\n" + "="*50)
print("测试完成")
