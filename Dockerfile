# Build stage
FROM python:3.14-slim AS builder

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtualenv
RUN uv venv /opt/venv && \
    /opt/venv/bin/python -m pip install --upgrade pip && \
    uv pip install --python /opt/venv/bin/python -e .

# Runtime stage
FROM python:3.14-slim

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY src ./src
COPY main.py ./main.py

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=10s \
    CMD wget --quiet --tries=1 --spider http://localhost:8000/api/v1/health || exit 1

EXPOSE 8000

CMD ["python", "main.py"]
