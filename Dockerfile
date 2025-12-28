# 使用 Python 3.12 官方镜像作为基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.4 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# 将 Poetry 添加到 PATH
ENV PATH="$POETRY_HOME/bin:$PATH"

# 安装 Poetry
RUN pip install poetry==$POETRY_VERSION

# 优化构建缓存：先复制依赖文件
COPY pyproject.toml poetry.lock* ./

# 安装项目依赖（不安装开发依赖）
RUN poetry install --no-root --only main

# 复制项目源代码
COPY . .

# 创建数据目录（作为挂载点）
RUN mkdir -p /app/data

# 设置数据目录卷
VOLUME ["/app/data"]

# 暴露 Web 服务端口
EXPOSE 8000

# 运行 Web 服务
CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"]