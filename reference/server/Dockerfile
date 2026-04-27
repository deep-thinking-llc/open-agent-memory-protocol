FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir build setuptools wheel

# Copy project files
COPY pyproject.toml .

# Build the wheel
COPY src/ src/
RUN python -m build --wheel --no-isolation


FROM python:3.11-slim

WORKDIR /app

# Copy the built wheel from builder stage
COPY --from=builder /app/dist/*.whl /tmp/

# Install the wheel
RUN pip install --no-cache-dir /tmp/*.whl && rm /tmp/*.whl

# Expose the server port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python3 -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/health').status)" 2>/dev/null || exit 1

# Create directory for encryption keys (recommended volume mount)
VOLUME /app/keys

# Run with uvicorn
CMD ["uvicorn", "oamp_server.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
