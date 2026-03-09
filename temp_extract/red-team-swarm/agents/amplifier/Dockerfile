FROM kalilinux/kali-rolling

# Install required tools
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    metasploit-framework \
    nmap \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Initialize Metasploit database
RUN service postgresql start && \
    msfdb init && \
    service postgresql stop

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY app.py .
COPY exploit_modules.py .

RUN useradd -m -u 1000 agent
USER agent

EXPOSE 8080
CMD ["python3", "app.py"]
