# 主程序 expaliner.py - AI代码解释CLI工具
"""AI代码解释CLI工具

使用Deepseek API 分析和解释代码

用法:
    py explainer.py <文件路径> [--lines 行范围]
    
示例:
    py explainer.py test_code.py
    py explainer.py test_code.py --lines 10-20
    py explainer.py test_code.py -l 15
"""

import asyncio
import argparse
import sys
from pathlib import Path
import json    # 序列化/反序列化
import  aiohttp
# from anthropic import AsyncAnthropic  不兼容DEEPSEEK

from config import Config

class CodeExplainer:
    """代码解释器: 调用AI分析代码"""
    
    def __init__(self):
        """初始化:验证配置,创建API客户端"""
        # 验证配置
        Config.validate()
        
        # × 创建Anthropic客户端(连接Deepseek)
        # ✅ 改用 aiohttp（不再用 Anthropic SDK）
        self.api_url = f"{Config.BASE_URL}/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {Config.API_KEY}",
            "Content-Type": "application/json"
        }

        print("✅ 代码解释器初始化成功\n")
        
    def read_file(self, file_path: str, line_range: str = None) -> str:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
            line_range: 行范围, 格式"42-58" or "42"
            
        Return:
            代码内容
            
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 行范围格式错误
        """
        
        # 使用 pathlib处理路径
        path = Path(file_path)
        
        # 检查文件是否存在
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
         
        # 读取文件
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()  
        
        print(f"📖 读取文件: {file_path}")
        print(f"📄 文件总行数: {len(lines)}")
        
        # 如果指定了行范围， 提取对应行
        if line_range:
            start, end = self._parse_line_range(line_range, len(lines))
            code = "\n".join(lines[start-1:end]) 
            print(f"📍 分析范围: 第 {start}-{end} 行")
         
        else:
            code = content
            print(f"📍 分析范围: 整个文件")
        
        return code   
    
    def _parse_line_range(self, line_range: str, total_lines:int) -> tuple[int, int]:
        """
        解析行范围
        
        Args:
            line_range:  "42-58" 或 "42"
            total_lines: 文件总行数
            
        Return:
            (start, end) 元组(1-based索引)
            
        Raises:
            ValueError: 行范围格式错误或超出范围
        """
        
        try:
            if "-" in line_range:
                start,  end = map(int, line_range.split("-"))
            else:
                start = end = int(line_range)
                
            # 验证范围
            if start < 1 or end > total_lines or start > end:
                raise ValueError(
                    f"行范围无效: {line_range}\n"
                    f"文件共 {total_lines} 行，范围应为 1-{total_lines}"
                )
                
            return start, end
        
        except ValueError as  e:
            if "invalid literal" in str(e):
                raise ValueError(
                    f"行范围格式错误: {line_range}\n"
                    "正确格式: '42' 或 '42-58'"
                )
                
            raise  # 重新抛出其他的异常(else情况)
        
    def _build_prompt(self, code:str, file_path:str, line_range: str=None) -> str:
        """
        构建发送给AI的提示词
        
        Args:
            code: 代码内容
            file_path: 文件路径
            line_range: 行范围
            
        Return:
            完整的提示词
        """
        location = f"{file_path}"
        if line_range:
            location += f"(第 {line_range} 行)"
            
        prompt = f"""请作为资深代码审查专家,分析一下Python代码:
        
        **代码位置**: {location}

        **分析要求**:
        1. **功能说明**: 这段代码的主要功能是什么？
        2. **逻辑分析**: 关键步骤和实现思路
        3. **潜在问题**：
            - 可能的bug（边界情况、空值处理等）
            - 性能问题
            - 代码质量问题
        4. **改进建议**：具体的优化方案（附代码示例）

        **代码**:
        ```python
        {code}
        请用中文回答，重点突出实际问题和可行建议。
        """
        
        return prompt
    
    async def explain_code(self, code:str, file_path:str, line_range: str = None):
        """
        调用AI解释代码(流式输出)
        
        Args:
            code: 代码内容
            file_path: 文件路径
            line_range: 行范围
        """
        # 构建提示词
        prompt = self._build_prompt(code, file_path, line_range)
        
        print("\n" + "=" * 70)
        print("🤖 AI 分析结果")
        print("=" * 70 + "\n")
        
        try:
            # ✅ 构建请求payload(OpenAI格式)
            payload = {
                "model": Config.MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": Config.MAX_TOKENS,
                "temperature": Config.TEMPERATURE,
                "stream": True   # 流式输出
            }
            
            # ✅ 用 aiohttp 发起异步HTTP请求
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as  response:
                    
                    # 检查HTTP状态码
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
                    
                    # ✅ 流式读取响应（SSE格式）
                    # 改进： 按行读取
                    buffer = ""
                    async for line in response.content:
                       
                        line = line.decode('utf-8').strip()
                        
     
                        # 跳过空行
                        if not line:
                            continue
                        
                        # SSE格式: 每行以"data: "开头
                        if not line.startswith("data: "):
                            continue
                        
                        data = line[6:]   # 去掉前缀
                        
                        # 检查结束标志    
                        if data == "[DONE]":
                            break
                            
                        try:
                            # 解析JSON
                            chunk = json.loads(data)
                            
                            # 提取内容(OpenAI格式)
                            if "choices" in chunk and len(chunk["choices"]) > 0 :
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                
                                # 实时输出
                                if content:
                                    print(content, end="", flush=True)
                                    
                        except json.JSONDecodeError:
                            #忽略无效JSON行
                            continue
                        
            print("\n\n" + "=" * 70)
            print("✅ 分析完成")
            print("=" * 70)
            
        # 错误处理
        except asyncio.TimeoutError:
            raise RuntimeError("请求超时")
            # sys.exit(1) 类方法不应该直接调用sys.exit()
        except aiohttp.ClientError as e:
            raise RuntimeError(f"网络错误: {e}")
        except Exception as e:
            raise RuntimeError(f"API调用失败: {e}")
    
async def main():
    """主函数： 解析参数， 执行代码分析"""
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(
        description="🔍 AI代码解释工具 - 使用Deepseek分析Python代码",
        formatter_class=argparse.RawDescriptionHelpFormatter, # 保持原始格式
        epilog="""
        示例:
        python explainer.py test_code.py              # 分析整个文件
        python explainer.py test_code.py --lines 10-20 # 分析第10-20行
        python explainer.py test_code.py -l 42        # 分析第42行
        """  # 尾部信息
        )
    
    # 位置参数: 文件路径
    parser.add_argument(
        "file",
        help="要分析的Python代码文件"
    )
    
    # 可选参数: 行范围
    parser.add_argument(
        "--lines", "-l",
        help="指定行范围(如 42-58 或 42)",
        default=None
    )
    
    # 解析参数
    args = parser.parse_args()
    
    # 如果是只显示配置
    #if args.show_config:
     #   Config.show()
      #  return
    
    try:
        # 创建解释器
        explainer = CodeExplainer()
        
        # 读取代码
        code = explainer.read_file(args.file, args.lines)
        
        # 解释代码
        await explainer.explain_code(code, args.file, args.lines)
        
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)  # 输出的标准错误流
        sys.exit(1)   # 程序退出
        
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
        