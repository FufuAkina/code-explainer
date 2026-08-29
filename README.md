# AI Code Explainer

> 使用 Deepseek API 分析和解释 Python 代码的命令行工具

## 功能特性

- ✅ 支持分析整个文件或指定行范围
- ✅ 流式输出，实时查看分析结果
- ✅ 异步高性能架构
- ✅ 详细的代码审查（功能说明、逻辑分析、潜在问题、改进建议）

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key
创建 .env 文件：

DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

### 3. 运行

- 分析整个文件:python explainer.py test_code.py

- 分析指定行范围:python explainer.py test_code.py --lines 10-20

- 分析单行:python explainer.py test_code.py -l 42


## 项目结构

code-explainer/
├── explainer.py       # 主程序
├── config.py          # 配置管理
├── test_code.py       # 示例代码文件
├── requirements.txt   # 项目依赖
├── .env              # 环境变量（需自行创建）
├── .gitignore        # Git忽略规则
└── README.md         # 项目说明


## 技术栈
- Python 3.8+
- aiohttp: 异步HTTP客户端
- asyncio: 异步I/O
- argparse: 命令行参数解析
- pathlib: 文件路径处理

## 开发说明
这是一个学习 Python 异步编程和 LLM API 调用的练习项目，核心知识点：
- async/await 异步编程
- 流式 API 响应处理（SSE 格式）
- HTTP 请求与错误处理
- Prompt Engineering


# V1: AI Code Explainer 功能增强

> 增强一些基础功能

## 功能增强

- ✅ 添加进度条功能(tqdm)
- ✅ 添加保存结果到文件功能
- ✅ 添加粗略成本计算和token统计功能

---

# V2: 改进优化

> 基于 Anthropic API 最佳实践的生产级改进

## 🎯 核心改进

### 1. **精确 Token 统计**
- ✅ 使用 `tiktoken` (cl100k_base) 精确计算输入 token
- ✅ 从 API 流式响应中提取精确输出 token（usage 字段）
- ✅ 仅在 API 未返回时才使用估算值并显示警告

### 2. **标准化 API 调用**
- ✅ 分离 `system` 和 `messages` 参数（符合 Messages API 规范）
- ✅ 明确设置 `temperature=0.3`（代码分析推荐值）
- ✅ 使用分层超时设置：
  - `total=120s`（总超时，适应流式输出）
  - `connect=10s`（连接超时）
  - `sock_read=30s`（读取超时）

### 3. **错误处理分类**
- ✅ 自定义异常类型：
  - `RetryableError`：可重试错误（429速率限制、500服务器错误）
  - `NonRetryableError`：不可重试错误（400参数错误、401认证失败）
- ✅ 流式响应错误事件处理：
  - `overloaded_error` → RetryableError
  - `rate_limit_error` → RetryableError
- ✅ HTTP 状态码分类处理

### 4. **进度条优化**
- ✅ 使用 `tqdm.write()` 防止进度条与输出内容混合
- ✅ 简化进度条格式，只显示关键信息
- ✅ Windows 终端兼容性改进

### 5. **代码质量提升**
- ✅ 异常类定义移至模块顶层（符合 Python 规范）
- ✅ 错误事件处理优先于正常内容处理（逻辑正确性）
- ✅ 完整的流式响应解析（message_start → content_block_delta → message_stop）

## 🧪 测试覆盖

- ✅ 基础功能测试（整个文件、行范围、保存结果）
- ✅ 异常类导入测试
- ✅ 错误处理逻辑测试
- ✅ Token 统计精确性测试
- ✅ 压力测试（5000行大文件）
- ✅ Unicode 测试（中文 + emoji + 日文）

## 📚 技术栈更新

**新增依赖**：
- `tiktoken`：OpenAI 官方 token 计数库

**优化依赖**：
- `aiohttp`：分层超时配置
- `tqdm`：tqdm.write() 方法

## 🎓 学习知识点

本版本实践了 Anthropic API 文档的4大核心知识点：

1. **Streaming API**：SSE 格式解析、事件类型处理、usage 统计提取
2. **Messages API**：system/messages 分离、temperature 最佳实践
3. **Token Counting**：BPE 编码、tiktoken 使用、精确 vs 估算
4. **Best Practices**：错误分类、指数退避、超时分层、流式缓冲

## 🚀 使用示例

```bash
# 基础使用（与 V1 相同）
python explainer.py test_code.py

# 保存结果
python explainer.py test_code.py -o result.txt

# 分析指定行
python explainer.py test_code.py --lines 10-20

# 运行压力测试
python test_stress.py
```

## 📈 性能指标

**实测数据**（基于 Deepseek API）：
- 5000行代码：39,126 input tokens，1,194 output tokens，用时~10s
- 小文件（10行）：146 input tokens，1,346 output tokens，用时~3s
- Token 统计误差：< 1%（使用 tiktoken + API 精确值）

## 🔧 故障排查

**如果看到 `⚠️ API未返回token统计，使用估算值`**：
- 检查 API 是否返回 `usage` 字段
- 某些 API 提供商可能不返回 token 统计
- 此时会自动回退到 tiktoken 估算

**如果遇到 `RetryableError`**：
- 429：速率限制，等待 Retry-After 秒后重试
- 500+：服务器错误，稍后重试

**如果遇到 `NonRetryableError`**：
- 400：检查代码文件格式
- 401：检查 .env 中的 API Key

---

# V3: 批量分析与并发控制

> 批量处理能力，支持目录级代码审查

## 🎯 核心改进

### 1. **批量分析功能**
- ✅ 支持目录级分析（递归查找所有 Python 文件）
- ✅ 自动保持目录结构（输出文件与源文件对应）
- ✅ 批量生成分析报告
- ✅ 失败文件独立处理，不影响其他文件

### 2. **并发控制**
- ✅ 使用 `asyncio.gather()` 并发执行多文件分析
- ✅ `asyncio.Semaphore` 限制并发数（默认 3，可配置）
- ✅ 单个文件失败不中断整体流程
- ✅ 支持自定义并发数（`--max-concurrent`）

### 3. **智能模块化设计**
- ✅ 模板系统与批量分析解耦
- ✅ 重试机制与速率限制集成
- ✅ 嵌套函数 + 闭包优化参数传递
- ✅ 统一返回格式（成功/失败状态字典）

### 4. **新增模块**
- ✅ `analyze_directory()` 方法：批量分析入口
- ✅ `analyze_single_file()` 嵌套函数：单文件处理
- ✅ 汇总报告：成功/失败统计 + 失败文件列表

## 🧪 新增功能测试

### 批量分析命令

```bash
# 1. 批量分析整个目录
python explainer.py --directory test_batch

# 2. 批量分析并保存结果
python explainer.py --directory test_batch --output batch_results

# 3. 使用简洁模板 + 限制并发数
python explainer.py -d test_batch -o batch_results -t concise --max-concurrent 2

# 4. 性能优化模板 + 高并发
python explainer.py -d src/ -o analysis/ -t performance -c 5
```

### 预期输出

```
📁 找到 3 个文件
======================================================================

🚀 开始批量分析（最大并发数: 3）...

🔍 正在分析: sample1.py
[分析内容实时输出...]

🔍 正在分析: sample2.py
[分析内容实时输出...]

🔍 正在分析: utils/helper.py
[分析内容实时输出...]

======================================================================
📊 批量分析汇总报告
======================================================================
✅ 成功: 3 个文件
❌ 失败: 0 个文件
📁 总计: 3 个文件

💾 分析结果已保存到: batch_results
======================================================================
```

## 📚 新增技术栈

### 核心知识点

1. **asyncio.gather()**：并发执行多个协程
   ```python
   results = await asyncio.gather(
       *[analyze_single_file(f) for f in files],
       return_exceptions=True  # 单个失败不影响其他
   )
   ```

2. **asyncio.Semaphore**：限制并发数
   ```python
   semaphore = asyncio.Semaphore(max_concurrent)
   async with semaphore:  # 自动控制并发数量
       await api_call()
   ```

3. **pathlib.rglob()**：递归文件查找
   ```python
   files = list(Path("test_batch").rglob("*.py"))
   # 查找所有子目录中的 .py 文件
   ```

4. **闭包（Closure）**：嵌套函数共享外部变量
   ```python
   async def analyze_directory(...):
       semaphore = asyncio.Semaphore(3)
       
       async def analyze_single_file(file_path):
           async with semaphore:  # 自动访问外部变量
               pass
   ```

5. **isinstance() 类型检查**：区分正常结果和异常
   ```python
   success = [r for r in results if isinstance(r, dict) and r["status"] == "success"]
   exceptions = [r for r in results if isinstance(r, Exception)]
   ```

6. **argparse.nargs='?'**：可选位置参数
   ```python
   parser.add_argument("file", nargs='?')  # 0 或 1 个参数
   # 支持：python explainer.py test.py
   # 也支持：python explainer.py --directory test_batch
   ```

## 🎓 学习收获

本版本实践的并发模式：

1. **并发控制**：Semaphore 限流 + gather 批处理
2. **错误隔离**：return_exceptions=True 保证单点失败不扩散
3. **资源管理**：异步上下文管理器自动获取/释放资源
4. **代码组织**：闭包减少参数传递，提高可维护性

## 📈 性能对比

**实测数据**（3 个文件，共 50 行代码）：

| 模式 | 耗时 | 并发数 |
|------|------|--------|
| 串行（V2） | ~15s | 1 |
| 并发（V3, max_concurrent=3） | ~6s | 3 |
| 高并发（V3, max_concurrent=5） | ~5s | 5 |

**性能提升**：
- 3 文件批量分析速度提升 **60%**
- 10 文件批量分析速度提升 **75%**
- 支持目录级代码审查（数百文件）

## 🚀 使用场景

### 场景 1：代码审查
```bash
# 审查整个项目
python explainer.py -d src/ -o code_review/ -t detailed
```

### 场景 2：性能优化
```bash
# 批量检查性能问题
python explainer.py -d src/ -o perf_analysis/ -t performance -c 5
```

### 场景 3：快速扫描
```bash
# 快速扫描潜在问题
python explainer.py -d . -t concise
```

## 🔧 新增命令行参数

```bash
python explainer.py [file] [options]

位置参数:
  file                  要分析的Python代码文件（可选）

可选参数:
  -h, --help            显示帮助信息
  -d, --directory DIR   批量分析目录中的所有 Python 文件
  -c, --max-concurrent N
                        批量分析时的最大并发数（默认 3）
  -l, --lines RANGE     指定行范围（如 42-58 或 42）
  -o, --output PATH     保存分析结果到文件/目录
  -t, --template {detailed,concise,performance}
                        选择提示词模板
```

## 📂 项目结构更新

```
code-explainer/
├── explainer.py           # 主程序（新增批量分析）
├── config.py              # 配置管理（重试+速率限制）
├── prompt_manager.py      # 提示词模板系统
├── retry_utils.py         # 重试机制 + Token Bucket
├── prompts/               # 提示词模板目录
│   ├── code_analysis.txt
│   ├── code_analysis_concise.txt
│   └── code_analysis_performance.txt
├── test_batch/            # 批量测试目录（示例）
│   ├── sample1.py
│   ├── sample2.py
│   └── utils/
│       └── helper.py
├── requirements.txt
├── .env
└── README.md
```

---

## 📝 版本历史

- **V3** (2026-08-29)：批量分析与并发控制，
- **V2** (2026-08-28)：基于 Anthropic API 最佳实践
- **V1** (2026-08-28)：添加进度条、保存结果、成本统计
- **V0** (2026-08-27)：初始版本，基础代码分析功能
