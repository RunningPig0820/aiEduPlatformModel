# AI 服务 (FastAPI, 答疑 + RAG 引擎) — Python 3.13
FROM python:3.13-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/app

# 依赖 (腾讯云 PyPI 镜像优先, 失败回退默认源)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
      -i https://mirrors.cloud.tencent.com/pypi/simple/ --timeout 120 \
    || pip install --no-cache-dir -r requirements.txt

# 服务代码
COPY main.py .
COPY api ./api
COPY core ./core
COPY models ./models
COPY config ./config
# RAG 运行时懒加载 run_eval + 切片数据(BM25/keymap) + 评测集
COPY scripts/rag ./scripts/rag

EXPOSE 9527
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9527"]
