FROM golang:1.24.1 as builder

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv

# Set working directory
WORKDIR /app

# Copy go mod and sum files
COPY whatsapp-bridge/go.mod whatsapp-bridge/go.sum ./whatsapp-bridge/

# Download all dependencies
RUN cd whatsapp-bridge && go mod download

# Copy the source code
COPY whatsapp-bridge ./whatsapp-bridge
COPY whatsapp-mcp-server ./whatsapp-mcp-server
COPY direct_proxy.py /app/

# Create Python virtual environment and install dependencies
RUN python3 -m venv /app/venv
RUN /app/venv/bin/pip install --upgrade pip
RUN /app/venv/bin/pip install -r whatsapp-mcp-server/requirements.txt
RUN /app/venv/bin/pip install fastapi uvicorn python-dotenv httpx

# Create directory for persistent storage
RUN mkdir -p /app/whatsapp-bridge/store

# Expose the port that Render will scan for
EXPOSE 8000

# Set the startup command to use the proxy server
CMD ["/app/venv/bin/python", "/app/direct_proxy.py"]