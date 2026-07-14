FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（PyMuPDF 需要 libmupdf 间接依赖）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY src/ ./src/
COPY alembic.ini .
COPY alembic/ ./alembic/

# 创建上传目录
RUN mkdir -p /app/src/uploads

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
