FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.11.28 /uv /uvx /bin/

# Cette couche ne change que si les dépendances changent
COPY pyproject.toml uv.lock README.md ./

RUN uv sync \
    --frozen \
    --no-dev \
    --no-install-project

# Le code est copié après l'installation des dépendances
COPY src ./src

# Installation du projet uniquement
RUN uv sync \
    --frozen \
    --no-dev

EXPOSE 8080

CMD ["uvicorn", "coach_ai.main:app", "--host", "0.0.0.0", "--port", "8080"]