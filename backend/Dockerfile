FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml ./
COPY ai_scientist ./ai_scientist
COPY examples ./examples
COPY tests ./tests

RUN pip install -e ".[dev]"

EXPOSE 8000
CMD ["uvicorn", "ai_scientist.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
