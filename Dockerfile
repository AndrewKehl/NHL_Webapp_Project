FROM python:3.9-slim-buster

# Install dependencies
RUN apt-get update && \
    apt-get install -y build-essential && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt

# Copy the app code
WORKDIR /app
COPY main.py /app

# Expose port 8050
EXPOSE 8050

# Start the app
CMD ["python", "main.py"]
