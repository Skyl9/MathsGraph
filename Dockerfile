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

