# Dockerfile

# 1. Use an official Python runtime as a parent image
FROM python:3.11-slim-bullseye as base

# 2. Set environment variables
# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures Python output is sent straight to the terminal without buffering
ENV PYTHONUNBUFFERED 1

# 3. Set the working directory in the container
WORKDIR /app

# 4. Install dependencies
# Copy only the requirements file to leverage Docker cache
COPY requirements.txt .
# Upgrade pip and install requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

RUN pip install pydantic

# 5. Copy the rest of the application code
# Copy the current directory contents into the container at /app
COPY . /app

# 6. Expose the port the app runs on
# Make sure this matches the port in the CMD instruction (or run.py if used)
EXPOSE 5002

# 7. Define the command to run the application
# Use uvicorn directly for production.
# --host 0.0.0.0 makes it accessible from outside the container.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5002"] 