FROM python:3.11-slim

# Install system dependencies for validation tools
RUN apt-get update && apt-get install -y \
    nmap \
    nikto \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY validation_modules.py .

RUN useradd -m -u 1000 agent
USER agent

EXPOSE 8080
CMD ["python", "app.py"]
