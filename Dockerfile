# 多阶段构建：第一阶段 - 构建环境
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖到临时目录
RUN pip install --no-cache-dir --user -r requirements.txt


# 第二阶段：运行环境（更小的镜像）
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 从构建阶段复制已安装的依赖
COPY --from=builder /root/.local /root/.local

# 复制应用代码
COPY explainer.py .
COPY config.py .
COPY prompt_manager.py .
COPY retry_utils.py .
COPY prompts/ ./prompts/

# 设置环境变量
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    DEEPSEEK_API_KEY="" \
    DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"

# 创建挂载点目录
RUN mkdir -p /workspace /output

# 设置入口点
ENTRYPOINT ["python", "explainer.py"]

# 默认参数（可被覆盖）
CMD ["--help"]
