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
import json # 序列化/反序列化
from pathlib import Path

import  aiohttp
from tqdm import tqdm # 加进度条功能
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
    
    def _estimate_tokens(self, text: str) -> int:
        """粗略估计token数(1 token ≈ 1.5个中文字符)"""
        chinese_chars = len([c for c in text if '\u4e00' <= c <= "\u9fff"]) # Unicode中文字符范围
        english_chars = len([c for c in text if c.isalpha()])
        
        # 中文: 1.5字符/token, 英文: 4字符/token
        estimated = (chinese_chars / 1.5) + (english_chars / 4)
        return int(estimated)
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> dict:
        """计算API调用成本
        
        deepseek-v4-flash定价 (高峰时段):
        -输入： 0.0001 / K tokens (缓存命中)
        -输出:  0.009元 / K tokens
            
        """
        input_cost = (input_tokens / 1000) *  0.0001
        output_cost = (output_tokens / 1000) * 0.009
        total_cost = input_cost + output_cost
        
        return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "input_cost_cny": input_cost,
        "output_cost_cny": output_cost,
        "total_cost_cny": total_cost,
        "total_cost_usd": total_cost / 7.2  # 假设汇率
    }
    
    async def explain_code(self, code:str, file_path:str, line_range: str = None, output_file: str = None):
        """
        调用AI解释代码(流式输出)
        
        Args:
            code: 代码内容
            file_path: 文件路径
            line_range: 行范围
        """
        # 构建提示词
        prompt = self._build_prompt(code, file_path, line_range)
        # 估算输入token
        input_tokens = self._estimate_tokens(prompt)
        
        print("\n" + "=" * 70)
        print("🤖 AI 分析结果")
        print("=" * 70 + "\n")
        print("⏳ 分析中，请稍候...\n") 
        
        # ✅ 用于保存结果
        full_response = []
        char_count = 0
        
        try:
            # ✅ 构建请求payload(OpenAI格式)
            payload = {
                "model": Config.MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": Config.MAX_TOKENS,
                "temperature": Config.TEMPERATURE,
                "stream": True   # 流式输出
            }
            
            # ✅ 添加进度条
            with tqdm(
                desc="📊 进度", 
                unit="字", 
                leave=False, # 完成后自动清除
                mininterval=0.5, # 减少刷新，每0.5秒刷新一次
                bar_format='{desc}: {n}字 | 用时{elapsed} ' # 简化格式
                ) as pbar:
                
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
                            
                            # ✅ 替换成详细错误处理
                            if response.stats == 401:
                                raise RuntimeError(
                                    "API认证失败\n"
                                    "请检查:\n"
                                    "1. .env文件中的DEEPSEEK_API_KEY是否正确\n"
                                    "2. API Key是否有效（未过期/未欠费）"
                                )
                            elif response.status == 429:
                                raise RuntimeError(
                                    "请求频率超限\n"
                                    "请稍后再试，或升级API套餐"
                                )
                            elif response.status == 500:
                                raise RuntimeError(
                                    "服务器错误\n"
                                    "Deepseek服务暂时不可用，请稍后重试"
                                )
                            else:
                                raise RuntimeError(
                                    f"HTTP {response.status}: {error_text}\n"
                                    "详细错误信息请查看上方"
                                )
                            
                        
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
                                        pbar.update(len(content))
                                        # ⭐ 使用 tqdm.write() 输出内容(防止与进度条混合)
                                        pbar.write(content, end="")
                                        full_response.append(content) # 收集响应
                                        char_count += len(content)
                                        
                            except json.JSONDecodeError as e:
                                #忽略无效JSON行
                                print(f"\n⚠️  警告: 跳过无效JSON数据", file=sys.stderr)
                                continue
            
            # 计算输出token  
            response_text = "".join(full_response)
            output_tokens = self._estimate_tokens(response_text)
                   
            print("\n\n" + "=" * 70)
            print("✅ 分析完成")
            
            # ✅ 显示统计信息
            cost_info = self._calculate_cost(input_tokens, output_tokens)
            print(f"\n📊 统计信息:")
            print(f"  • 输出字符数: {char_count}")
            print(f"  • 输入 tokens: {cost_info['input_tokens']}")
            print(f"  • 输出 tokens: {cost_info['output_tokens']}")
            print(f"  • 总计 tokens: {cost_info['total_tokens']}")
            print(f"  • 预估成本: ¥{cost_info['total_cost_cny']:.4f} (${cost_info['total_cost_usd']:.4f})")
            
            # ✅ 保存到文件
            if output_file:
                Path(output_file).write_text(response_text, encoding="utf-8")
                print(f"💾 结果已保存到: {output_file}")
                
            print("=" * 70)
            
        # 错误处理
        except asyncio.TimeoutError:
            raise RuntimeError(
                "请求超时(>60秒)\n"
                "可能原因:\n"
                "1. 网络连接不稳定\n"
                "2. 代码文件过大\n"
                "3. API服务响应慢\n"
                "建议: 尝试分析更小的代码段"
            )
        except aiohttp.ClientError as e:
            raise RuntimeError(
                f"网络连接错误: {e}\n"
                "请检查:\n"
                "1. 网络连接是否正常\n"
                "2. 是否需要代理设置"
            )
        except Exception as e:
            raise RuntimeError(f"API调用失败: {type(e).__name__}: {e}")
    
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
    
    # 添加 --output参数，添加保存结果功能
    parser.add_argument(
        "--output", "-o",
        help="保存分析结果到文件",
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
        await explainer.explain_code(code, args.file, args.lines, args.output)
        
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
        