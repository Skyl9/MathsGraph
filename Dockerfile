# Use a lightweight official Python image as the base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install dependencies from requirements.txt
# This layer is cached if the file doesn't change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code into the container
# The 'app' folder and its contents are copied to /app/app
COPY ./app /app/app

# Command to run your FastAPI application using Uvicorn
# The --port $PORT part is crucial for Railway, as it uses a dynamic port
CMD uvicorn app.main:app --host 0.0.0.0