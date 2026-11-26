FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir '.[cloud]' && useradd --create-home atlas && mkdir workspace && chown atlas:atlas workspace
USER atlas
ENV ENVIRONMENT=production LLM_PROVIDER=fastembed CHAT_PROVIDER=groq CODEATLAS_WORKSPACE_DIR=/app/workspace
ENV OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 RAYON_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false
CMD ["sh", "-c", "uvicorn codeatlas.api.app:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
