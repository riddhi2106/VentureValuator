FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH=/app/.venv/bin:$PATH \
    APP_ENV=production \
    TEST_MODE=false \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_HEADLESS=true

WORKDIR /app

RUN groupadd --system venturevaluator \
    && useradd --system --gid venturevaluator --create-home venturevaluator

COPY pyproject.toml uv.lock README.md ./
COPY agents ./agents
COPY app ./app
COPY core ./core
COPY tools ./tools
COPY mcp_server.py ./

RUN python -m pip install uv==0.12.0 \
    && uv sync --frozen --no-dev --no-editable

RUN mkdir -p /app/memory /app/outputs \
    && chown -R venturevaluator:venturevaluator /app

USER venturevaluator

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)"

CMD ["streamlit", "run", "app/ui.py"]
