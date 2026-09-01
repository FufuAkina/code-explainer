# Code Explainer

一个基于 DeepSeek AI 的 Python 代码分析工具，支持单文件和批量目录分析，具备流式输出、重试机制和速率限制功能。

## 功能特性

- ✅ **单文件分析**：深度解析单个 Python 文件
- ✅ **批量分析**：并发处理整个目录
- ✅ **流式输出**：实时显示 AI 分析结果
- ✅ **智能重试**：自动处理 API 错误和速率限制
- ✅ **Token Bucket 限流**：防止超出 API 速率限制
- ✅ **Docker 部署**：容器化运行，环境隔离
- ✅ **完善测试**：单元测试覆盖率 36%+

---

## 快速开始

### 方式一：本地运行

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 配置环境变量

创建 `.env` 文件：

```bash
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

#### 3. 运行

```bash
# 分析单个文件
python explainer.py analyze test.py

# 分析整个目录
python explainer.py batch . --pattern "*.py"
```

---

### 方式二：Docker 部署

#### 1. 构建镜像

```bash
docker build -t code-explainer:latest .
```

**镜像优化**：
- 使用多阶段构建：`builder` + `runtime`
- 最终镜像大小：**265MB**（相比单阶段减少 100MB）

#### 2. 运行容器

**基础用法**：

```bash
docker run --rm \
  -e DEEPSEEK_API_KEY=your_key \
  -v /path/to/code:/workspace \
  code-explainer:latest analyze /workspace/test.py
```

**批量分析**：

```bash
docker run --rm \
  -e DEEPSEEK_API_KEY=your_key \
  -v $(pwd):/workspace \
  -v $(pwd)/output:/output \
  code-explainer:latest batch /workspace --output-dir /output
```

**使用 .env 文件**：

```bash
docker run --rm \
  --env-file .env \
  -v $(pwd):/workspace \
  code-explainer:latest analyze /workspace/test.py
```

#### 3. Docker Compose（推荐）

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  code-explainer:
    build: .
    image: code-explainer:latest
    env_file: .env
    volumes:
      - ./code:/workspace
      - ./output:/output
    command: ["batch", "/workspace", "--output-dir", "/output"]
```

运行：

```bash
docker-compose up
```

---

## 测试

### 运行所有测试

```bash
pytest test_core.py -v
```

### 查看覆盖率

```bash
pytest test_core.py --cov=. --cov-report=html
# 打开 htmlcov/index.html 查看详细报告
```

### 测试覆盖

| 模块 | 覆盖率 | 说明 |
|------|--------|------|
| `explainer.py` | 39% | API 调用、流式解析 |
| `retry_utils.py` | 56% | 重试机制、Token Bucket |
| `config.py` | 63% | 配置管理 |
| `prompt_manager.py` | 55% | 提示词模板 |

**测试用例**：
- ✅ `test_api_call_success` - API 正常调用
- ✅ `test_api_call_429_error` - 速率限制处理
- ✅ `test_api_call_500_error` - 服务器错误处理
- ✅ `test_retry_success_after_failure` - 重试成功
- ✅ `test_retry_max_attempts` - 最大重试次数
- ✅ `test_token_bucket_rate_limit` - Token Bucket 限流
- ✅ `test_token_bucket_refill` - Token Bucket 自动补充

---

## 项目结构

```
code-explainer/
├── explainer.py          # 主程序：CLI 和核心逻辑
├── config.py             # 配置管理
├── prompt_manager.py     # 提示词模板管理
├── retry_utils.py        # 重试装饰器和 Token Bucket
├── requirements.txt      # Python 依赖
├── Dockerfile            # Docker 镜像构建
├── .dockerignore         # Docker 构建排除文件
├── pytest.ini            # pytest 配置
├── test_core.py          # 核心功能单元测试
├── prompts/              # 提示词模板目录
│   ├── detailed.txt
│   ├── quick.txt
│   └── security.txt
└── README.md
```

---

## 核心技术

### 1. 异步 HTTP 请求

使用 `aiohttp` 进行异步 API 调用，支持流式响应（SSE）：

```python
async with session.post(url, json=payload) as response:
    async for line in response.content:
        # 实时处理流式数据
        chunk = json.loads(line)
        content = chunk["choices"][0]["delta"]["content"]
```

### 2. 重试机制

指数退避重试装饰器：

```python
@retry(max_attempts=3, base_delay=1.0, max_delay=60.0)
async def explain_code(...):
    # 自动重试 RetryableError、TimeoutError、ClientError
```

**退避策略**：
- 第 1 次重试：延迟 1 秒
- 第 2 次重试：延迟 2 秒
- 第 3 次重试：延迟 4 秒

### 3. Token Bucket 限流

防止 API 速率限制：

```python
bucket = TokenBucket(rate=5, capacity=5)  # 每秒最多 5 个请求

async with bucket:
    await api_call()  # 自动限流
```

**原理**：
- 初始令牌：`capacity` 个
- 补充速率：每秒 `rate` 个
- 请求消耗 1 个令牌，不足时等待

---

## Docker 详解

### Dockerfile 解析

```dockerfile
# 第一阶段：构建环境
FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# 第二阶段：运行环境
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY explainer.py config.py prompt_manager.py retry_utils.py .
COPY prompts/ ./prompts/
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    DEEPSEEK_API_KEY="" \
    DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"
RUN mkdir -p /workspace /output
ENTRYPOINT ["python", "explainer.py"]
CMD ["--help"]
```

**关键技术**：
- **多阶段构建**：分离构建和运行环境，减少镜像体积
- **ENTRYPOINT vs CMD**：
  - `ENTRYPOINT`：固定入口点（`python explainer.py`）
  - `CMD`：默认参数（`--help`），可被覆盖
- **环境变量**：通过 `docker run -e` 注入
- **卷挂载**：`-v` 挂载本地目录到容器

### .dockerignore

排除不必要的文件，加速构建：

```
venv/
__pycache__/
*.pyc
.git/
test_*.py
result.txt
batch_results/
```

---

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | 必填 |
| `DEEPSEEK_BASE_URL` | API 基础 URL | `https://api.deepseek.com/v1` |
| `DEEPSEEK_MODEL` | 使用的模型 | `deepseek-chat` |
| `MAX_TOKENS` | 最大输出 token 数 | `2000` |
| `TEMPERATURE` | 生成温度 | `0.7` |
| `RETRY_MAX_ATTEMPTS` | 最大重试次数 | `3` |
| `RETRY_BASE_DELAY` | 重试基础延迟（秒） | `1.0` |
| `RETRY_MAX_DELAY` | 重试最大延迟（秒） | `60.0` |

---

## 常见问题

### 1. Docker 镜像构建失败：找不到 requirements.txt

**问题**：`.dockerignore` 中的 `*.txt` 排除了 `requirements.txt`

**解决**：
```bash
# 修改 .dockerignore，改为具体文件名
result.txt
# 而不是 *.txt
```

### 2. pytest 异步测试失败："async def functions are not natively supported"

**问题**：缺少 `pytest-asyncio` 配置

**解决**：创建 `pytest.ini`：
```ini
[pytest]
asyncio_mode = auto
```

### 3. Docker 容器内无法访问本地文件

**问题**：没有挂载卷

**解决**：
```bash
docker run -v $(pwd):/workspace code-explainer analyze /workspace/test.py
```

### 4. API Key 无效错误

**问题**：环境变量未正确传递

**解决**：
```bash
# 方式1：-e 传递
docker run -e DEEPSEEK_API_KEY=sk-xxx ...

# 方式2：--env-file
docker run --env-file .env ...
```

---

## 开发指南

### 添加新的提示词模板

1. 在 `prompts/` 目录创建 `.txt` 文件
2. 在 `prompt_manager.py` 中注册：

```python
self.templates = {
    "detailed": "prompts/detailed.txt",
    "quick": "prompts/quick.txt",
    "your_template": "prompts/your_template.txt",  # 新增
}
```

### 运行单个测试

```bash
pytest test_core.py::test_api_call_success -v
```

### 调试模式

```bash
# 显示详细日志
export DEBUG=1
python explainer.py analyze test.py
```

---

## 更新日志

### v1.0.0 (2026-09-01)
- ✅ 实现单文件和批量分析
- ✅ 添加 Docker 支持（多阶段构建）
- ✅ 完善单元测试（覆盖率 36%+）
- ✅ 添加重试机制和 Token Bucket 限流
- ✅ 支持流式输出和进度条

