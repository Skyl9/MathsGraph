# Use a lightweight official Python image as the base
FROM python:3.12-slim


# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app
RUN uv sync --frozen --no-cache

# The --port $PORT part is crucial for Railway, as it uses a dynamic port
CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--port $PORT", "--host", "0.0.0.0"]
