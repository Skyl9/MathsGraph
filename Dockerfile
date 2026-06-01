# Use a lightweight official Python image as the base
FROM python:3.13-slim

# Install PostgreSQL system dependencies
RUN apt-get update && apt-get install -y libpq5 && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app
RUN uv sync --frozen --no-cache

# Expose the port so Railway's proxy knows where to route traffic
EXPOSE 8000

# Run with uvicorn in production mode (Railway injects $PORT dynamically)
CMD /app/.venv/bin/uvicorn app.main:app --host :: --port ${PORT:-8000} --workers 2