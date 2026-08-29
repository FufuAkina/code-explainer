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

import aiohttp
import tiktoken
from tqdm import tqdm # 加进度条功能
# from anthropic import AsyncAnthropic  不兼容DEEPSEEK

from config import Config
from prompt_manager import PromptManager   # 提示词管理模块
from retry_utils import retry, TokenBucket # 重试装饰器+速率限制器

# 自定义异常类型
class RetryableError(Exception):
    """可重试的错误"""
    pass

class NonRetryableError(Exception):
    """不可重试的错误"""
    pass
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
        self.encoding = tiktoken.get_encoding("cl100k_base")
        self.prompt_manager = PromptManager(Config.PROMPTS_DIR)
        self.rate_limiter = None
        if Config.RATE_LIMIT_ENABLED:
            self.rate_limiter = TokenBucket(
                rate=Config.RATE_LIMIT_RATE,
                capacity=Config.RATE_LIMIT_CAPACITY
            )
            print(f"✅ 速率限制已启用: {Config.RATE_LIMIT_RATE} 请求/秒")

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
        
    def _estimate_tokens(self, text: str) -> int:
        """使用tiktoken精确计算token数"""
        return len(self.encoding.encode(text))
    
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
        
    # 用装饰器包装API调用
    @retry(
        max_attempts=Config.RETRY_MAX_ATTEMPTS,
        base_delay=Config.RETRY_BASE_DELAY,
        max_delay=Config.RETRY_MAX_DELAY,
        retryable_exceptions=(RetryableError, asyncio.TimeoutError, aiohttp.ClientError)
    )
    async def explain_code(
        self,
        code: str, 
        file_path: str, 
        line_range: str = None, 
        output_file: str = None,
        template: str = None):
        """
        调用AI解释代码(流式输出)
        
        Args:
            code: 代码内容
            file_path: 文件路径
            line_range: 行范围
        """
        # 构建提示词
        template_name = template or Config.DEFAULT_TEMPLATE
        prompt = self.prompt_manager.build_prompt(
            template_name, code, file_path, line_range
        )
        print(f"📝 使用模板: {template_name}")
        
        # 估算输入token
        input_tokens = self._estimate_tokens(prompt)
        
        print("\n" + "=" * 70)
        print("🤖 AI 分析结果")
        print("=" * 70 + "\n")
        print("⏳ 分析中，请稍候...\n") 
        
        # ✅ 用于保存结果
        full_response = []
        char_count = 0
        output_tokens = 0  # 从API获取精确值
        
        try:
            # ✅ 构建请求payload(OpenAI格式)
            payload = {
                "model": Config.MODEL,
                "system": "你是一位拥有10年Python开发经验的资深工程师，擅长发现代码中的边界条件问题和性能瓶颈。",
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
                        timeout=aiohttp.ClientTimeout(
                            total=120,    # 总超时
                            connect=10,   # 连接超时
                            sock_read=30, # 读取超时
                            )
                    ) as  response:
                        
                        # 检查HTTP状态码
                        if response.status != 200:
                            error_text = await response.text()
                            
                            # 1. HTTP状态码分类
                            if response.status == 400:
                                # 客户端错误 - 不应重试
                                raise ValueError("请求参数错误，请检查输入")
                            elif response.status == 401:
                                # 认证错误 - 不应重试
                                raise RuntimeError("API Key无效")
                            elif response.status == 429:
                                # 速率限制 - 应该重试（带退避）
                                retry_after = response.headers.get("Retry-After", 60)
                                raise RetryableError(f"速率限制，{retry_after}秒后重试")
                            elif response.status >= 500:
                                # 服务器错误 - 应该重试
                                raise RetryableError("服务器错误，稍后重试")
                            else:
                                # 其他错误
                                raise RuntimeError(f"HTTP {response.status}: {error_text}")
                                                   
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
                                
                                 # ✅ 1.检查是否是错误世间
                                if chunk.get("type") == "error":
                                    error_info = chunk.get("error", {})
                                    error_type = error_info.get("type")
                                    error_msg = error_info.get("message")
                                    
                                    if error_type == "overloaded_error":
                                        raise RetryableError(f"服务器过载: {error_msg}\n建议稍后重试")
                                    elif error_type == "rate_limit_error":
                                        raise RetryableError(f"速率限制: {error_msg}\n建议降低请求频率")
                                    else:
                                        raise RuntimeError(f"API错误: {error_msg}")
                                                            
                                # ✅ 2.处理正常内容
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
                                        
                                # ✅ 3.处理 token 使用量统计
                                if "usage" in chunk:
                                    usage = chunk["usage"]
                                    if "prompt_tokens" in usage:
                                        input_tokens = usage["prompt_tokens"]
                                    if "completion_tokens" in usage:
                                        output_tokens = usage["completion_tokens"]
                                        
                            except json.JSONDecodeError as e:
                                #忽略无效JSON行
                                print(f"\n⚠️  警告: 跳过无效JSON数据", file=sys.stderr)
                                continue
            
            # 不需要计算， 直接从API的SSE流中获取  
            response_text = "".join(full_response)
            
            if output_tokens == 0:
                output_tokens = self._estimate_tokens(response_text)
                print("⚠️  API未返回token统计，使用估算值", file=sys.stderr)
            
                   
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
    
    async def analyze_directory(
        self,
        directory: str,
        pattern: str = "*.py",
        output_dir: str = None,
        template: str = None,
        max_concurrent: int = 3
    ) -> dict:
        """批量分析目录中的所有 Python 文件
        
        Args:
            directory: 目录路径
            pattern: 文件匹配模式（默认 *.py）
            output_dir: 输出目录（可选）
            template: 提示词模板
            max_concurrent: 最大并发数
            
        Returns:
            分析结果汇总字典
        """
        # 查找所有匹配文件
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"目录不存在: {directory}")
        
        if not dir_path.is_dir():
            raise ValueError(f"不是目录: {directory}")
        
        # 递归查找所有 Python 文件
        files = list(dir_path.rglob(pattern))
        
        if not files:
            print(f"⚠️  未找到匹配的文件: {pattern}")
            return {"success":[], "failed": [], "total_cost": 0}
        
        print(f"\n📁 找到 {len(files)} 个文件")
        print("=" * 70)
        
        # 创建输出目录
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
        # 使用 Semaphore 限制并发数
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_single_file(file_path: Path) -> dict:
            """分析单个文件"""
            async with semaphore: # 限制并发
                try:
                    print(f"\n🔍 正在分析: {file_path.relative_to(dir_path)}")
                    
                    # 读取代码
                    code = file_path.read_text(encoding="utf-8")
                    
                    # 构建输出文件路径
                    output_file = None
                    if output_dir:
                        relative_path = file_path.relative_to(dir_path)
                        output_file = output_path / f"{relative_path.stem}_analysis.txt"
                        output_file.parent.mkdir(parents=True, exist_ok=True)
                        
                    # 分析代码
                    await self.explain_code(
                        code,
                        str(file_path),
                        template=template,
                        output_file=str(output_file) if output_file else None
                    )
                    
                    return{
                        "file": str(file_path),
                        "status": "success",
                        "error": None
                    }
                    
                except Exception as e:
                    print(f"❌ 分析失败: {file_path.name} - {e}", file=sys.stderr)
                    return {
                        "file": str(file_path),
                        "status": "failed",
                        "error": str(e)
                    }

        # 并发分析所有文件
        print(f"\n🚀 开始批量分析（最大并发数: {max_concurrent}）...")
        results = await asyncio.gather(
            *[analyze_single_file(f) for f in files],
            return_exceptions=True
        )

        # 统计结果
        success = [r for r in results if isinstance(r, dict) and r["status"] == "success"]
        failed = [r for r in results if isinstance(r, dict) and r["status"] == "failed"]
        exceptions = [r for r in results if isinstance(r, Exception)]

        # 打印汇总报告
        print("\n" + "=" * 70)
        print("📊 批量分析汇总报告")
        print("=" * 70)
        print(f"✅ 成功: {len(success)} 个文件")
        print(f"❌ 失败: {len(failed) + len(exceptions)} 个文件")
        print(f"📁 总计: {len(files)} 个文件")

        if failed:
            print("\n失败文件列表：")
            for r in failed:
                print(f"  • {Path(r['file']).name}: {r['error']}")

        if exceptions:
            print("\n异常文件列表:")
            for i, e in enumerate(exceptions):
                print(f"  • 文件 {i+1}: {e}")

        if output_dir:
            print(f"\n💾 分析结果已保存到: {output_dir}")

        print("=" * 70)

        return {
            "success": success,
            "failed": failed + [{"file": f"exception_{i}", "error":str(e)} for i, e in enumerate(exceptions)],
            "total_files": len(files),
            "success_count": len(success),
            "failed_count": len(failed) + len(exceptions)
        }
    
    
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
        nargs='?',  # 改为可选
        help="要分析的Python代码文件"
    )
    
    # 新增：目录分析参数
    parser.add_argument(
        "--directory", "-d",
        help="批量分析目录中的所有Python文件",
        default=None
    )
    # 新增： 并发数参数
    parser.add_argument(
        "--max-concurrent", "-c",
        type=int,
        help="批量分析时的最大并发数(默认 3)",
        default=3
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
    
    # 添加 --template 参数
    parser.add_argument(
        "--template", "-t",
        choices=["detailed", "concise", "performance"],
        help="选择提示词模板(详细/简洁/性能优化)",
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
        
        # 判断是目录分析还是单文件分析
        if args.directory:
            # 批量分析目录
            await explainer.analyze_directory(
                directory=args.directory,
                output_dir=args.output,
                template=args.template,
                max_concurrent=args.max_concurrent
            )
        elif args.file:
            # 单文件分析
            code = explainer.read_file(args.file, args.lines)
            await explainer.explain_code(
                code, args.file, args.lines, args.output, args.template
                )
        else:
            parser.print_help()
            sys.exit(1)
        
        
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
        