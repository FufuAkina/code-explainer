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

# V2: 企业级改进版本

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

## 📝 版本历史

- **V2** (2026-08-28)：企业级改进，基于 Anthropic API 最佳实践
- **V1** (2026-08-28)：添加进度条、保存结果、成本统计
- **V0** (2026-08-27)：初始版本，基础代码分析功能
