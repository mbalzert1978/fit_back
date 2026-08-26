# Build stage
FROM python:3.14-slim AS builder

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtualenv
#
# Kein `python -m pip install --upgrade pip` davor: `uv venv` legt bewusst kein
# pip in die Umgebung, der Aufruf scheiterte also mit "No module named pip".
# Gebraucht wird es auch nicht - `uv pip` bringt seine eigene Aufloesung mit.
RUN uv venv /opt/venv && \
    uv pip install --python /opt/venv/bin/python -e .

# Runtime stage
FROM python:3.14-slim

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY src ./src

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check
#
# Mit Python und nicht mit wget oder curl: python:3.14-slim bringt beides nicht
# mit, der alte Aufruf scheiterte mit "wget: not found". Ein `apt-get install`
# dafuer waere eine Schicht und ein Paket mehr im Laufzeit-Image, nur um eine
# HTTP-Anfrage zu stellen, die die Standardbibliothek auch stellt.
#
# `urlopen` wirft bei allem ausser 2xx - der Aufruf endet dann von selbst
# ungleich null, ein `|| exit 1` braucht es nicht.
HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=10s \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')"]

EXPOSE 8000

CMD ["python", "-m", "src.main"]
