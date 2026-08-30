"""单元测试：测试 CodeExplainer 核心功能"""

import pytest
import asyncio
from pathlib import Path
from explainer import CodeExplainer, RetryableError, NonRetryableError

# ========== 测试1：文件读取 ==========

def test_read_file_success():
    """测试读取存在的文件"""
    # 创建测试文件
    test_file = Path("test_temp.py")
    test_file.write_text("print('hello')\nprint('world')", encoding="utf-8")
    
    try:
        explainer = CodeExplainer()
        code = explainer.read_file(str(test_file))
        
        assert "print('hello')" in code
        assert "print('world')" in code
    finally:
        test_file.unlink()  # 清理


def test_read_file_with_line_range():
    """测试读取指定行范围"""
    test_file = Path("test_temp.py")
    test_file.write_text("line1\nline2\nline3\nline4", encoding="utf-8")
    
    try:
        explainer = CodeExplainer()
        code = explainer.read_file(str(test_file), "2-3")
        
        assert code == "line2\nline3"
    finally:
        test_file.unlink()


def test_read_file_not_found():
    """测试读取不存在的文件"""
    explainer = CodeExplainer()
    
    with pytest.raises(FileNotFoundError):
        explainer.read_file("nonexistent.py")


# ========== 测试2：行范围解析 ==========

def test_parse_line_range_single():
    """测试解析单行"""
    explainer = CodeExplainer()
    start, end = explainer._parse_line_range("42", 100)
    
    assert start == 42
    assert end == 42


def test_parse_line_range_multi():
    """测试解析多行"""
    explainer = CodeExplainer()
    start, end = explainer._parse_line_range("10-20", 100)
    
    assert start == 10
    assert end == 20


def test_parse_line_range_invalid():
    """测试无效行范围"""
    explainer = CodeExplainer()
    
    # 超出范围
    with pytest.raises(ValueError, match="行范围无效"):
        explainer._parse_line_range("1-200", 100)
    
    # 格式错误
    with pytest.raises(ValueError, match="行范围格式错误"):
        explainer._parse_line_range("abc", 100)


# ========== 测试3：Token 计算 ==========

def test_estimate_tokens():
    """测试 token 计算"""
    explainer = CodeExplainer()
    
    # 英文文本
    tokens_en = explainer._estimate_tokens("Hello world")
    assert tokens_en > 0
    assert tokens_en < 10  # 简单文本 token 数应该很少
    
    # 中文文本（token 数更多）
    tokens_cn = explainer._estimate_tokens("你好世界")
    assert tokens_cn > 0


def test_calculate_cost():
    """测试成本计算"""
    explainer = CodeExplainer()
    
    cost_info = explainer._calculate_cost(1000, 500)
    
    assert cost_info["input_tokens"] == 1000
    assert cost_info["output_tokens"] == 500
    assert cost_info["total_tokens"] == 1500
    assert cost_info["total_cost_cny"] > 0
    assert cost_info["total_cost_usd"] > 0


# ========== 测试4：提示词构建 ==========

def test_build_prompt():
    explainer = CodeExplainer()

    prompt = explainer.prompt_manager.build_prompt(
        "detailed",
        "print('test')",
        "test.py",
        "1-5"
    )

    assert "test.py" in prompt
    assert "1-5" in prompt
    assert "print('test')" in prompt

# ========== 测试5：异常类型 ==========

def test_exception_types():
    """测试自定义异常类型"""
    # 确保异常类可以正常导入和使用
    
    try:
        raise RetryableError("测试可重试错误")
    except RetryableError as e:
        assert str(e) == "测试可重试错误"
    
    try:
        raise NonRetryableError("测试不可重试错误")
    except NonRetryableError as e:
        assert str(e) == "测试不可重试错误"


# ========== 运行测试 ==========

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
