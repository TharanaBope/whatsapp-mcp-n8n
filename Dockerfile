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

# Create Python virtual environment and install dependencies
RUN python3 -m venv /app/venv
RUN /app/venv/bin/pip install --upgrade pip
RUN /app/venv/bin/pip install -r whatsapp-mcp-server/requirements.txt
RUN /app/venv/bin/pip install fastapi uvicorn

# Create directory for persistent storage
RUN mkdir -p /app/whatsapp-bridge/store

# Create a simple wrapper script to start both services
RUN echo '#!/bin/bash\n\
cd /app/whatsapp-bridge && go run main.go & \n\
cd /app/whatsapp-mcp-server && /app/venv/bin/python /app/healthcheck.py\n' > /app/start.sh && \
chmod +x /app/start.sh

# Create a health check server Python script
RUN echo 'import os\n\
import uvicorn\n\
from fastapi import FastAPI\n\
import subprocess\n\
import threading\n\
import time\n\
\n\
app = FastAPI()\n\
\n\
@app.get("/")\n\
def read_root():\n\
    return {"status": "ok", "message": "WhatsApp Bridge running"}\n\
\n\
def start_whatsapp_mcp():\n\
    time.sleep(2)  # Give the health check server time to start\n\
    env = os.environ.copy()\n\
    env["MCP_TRANSPORT"] = "stdio"\n\
    subprocess.run(["/app/venv/bin/python", "main.py"], env=env)\n\
\n\
# Start WhatsApp MCP in a separate thread\n\
thread = threading.Thread(target=start_whatsapp_mcp)\n\
thread.daemon = True\n\
thread.start()\n\
\n\
if __name__ == "__main__":\n\
    port = int(os.environ.get("PORT", 8000))\n\
    print(f"Starting health check server on port {port}")\n\
    uvicorn.run(app, host="0.0.0.0", port=port)\n' > /app/healthcheck.py

# Expose the port that Render will scan for
EXPOSE 8000

# Set the startup command to use our wrapper script
CMD ["/app/start.sh"]