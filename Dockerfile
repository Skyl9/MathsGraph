# Use a lightweight official Python image as the base
# The 'slim' version is smaller and faster to build
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
# This step is cached, so it only runs when requirements.txt changes
COPY requirements.txt .

# Install all dependencies from the requirements file
# --no-cache-dir reduces the image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Expose the port that your application will run on
# This should match the port configured in your run command
EXPOSE 8000

# Command to run your FastAPI application using Uvicorn
# The format is 'module:app_object --host 0.0.0.0 --port $PORT'
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
