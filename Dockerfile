# /usr/share/nginx/html/Dockerfile

FROM python:3.12-slim

# Set working directory
WORKDIR /usr/share/nginx/html

# Install system dependencies
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Create virtualenv and install dependencies
RUN python3 -m venv venv && \
    . venv/bin/activate && \
    pip install --no-cache-dir --upgrade pip && \
    pip uninstall -y bson pymongo || true && \
    pip install --no-cache-dir pymongo && \
    pip install --no-cache-dir -r requirements.txt

# Set environment to use virtualenv
ENV PATH="/usr/share/nginx/html/venv/bin:$PATH"

# Expose port
EXPOSE 8000

# Start the app
CMD ["python", "run.py"]
