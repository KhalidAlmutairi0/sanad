FROM python:3.12-slim

WORKDIR /app

COPY apps/embedder/requirements.txt ./requirements.txt
# CPU-only torch keeps the image reasonable for local + on-prem CPU deployments.
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

COPY apps/embedder/server.py ./server.py

ENV PYTHONUNBUFFERED=1 HF_HOME=/model-cache
EXPOSE 8081
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8081"]
