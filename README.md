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


