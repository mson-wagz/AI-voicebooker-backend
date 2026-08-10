FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    postgresql-client \
    wget \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*



# Set Chrome environment variables


COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen

COPY prisma/ ./prisma/
RUN uv run prisma generate

COPY src/ ./src/

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
