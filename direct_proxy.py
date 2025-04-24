import os
import sys
import uvicorn
from fastapi import FastAPI, Request, Response
import subprocess
import threading
import time
import httpx
import json
import logging
import re
from typing import Optional

# Determine base paths based on operating system
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
BRIDGE_PATH = os.path.join(BASE_PATH, "whatsapp-bridge")
MCP_SERVER_PATH = os.path.join(BASE_PATH, "whatsapp-mcp-server")
LOG_PATH = os.path.join(BASE_PATH, "qr_log.txt")

# Add whatsapp-mcp-server to Python path
sys.path.append(MCP_SERVER_PATH)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-proxy")

app = FastAPI()

# Store the WhatsApp session status
bridge_status = {
    "started": False,
    "authenticated": False,
    "qr_generated": False,
    "start_time": time.time(),
    "last_log_check": 0
}

@app.get("/")
def read_root():
    # Calculate uptime
    uptime = time.time() - bridge_status["start_time"]
    uptime_str = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s"
    
    return {
        "status": "ok", 
        "message": "WhatsApp Bridge running",
        "uptime": uptime_str,
        "authenticated": bridge_status["authenticated"],
        "qr_generated": bridge_status["qr_generated"]
    }

def get_qr_from_logs() -> Optional[str]:
    """Extract QR code from logs file"""
    try:
        if not os.path.exists(LOG_PATH):
            return None
            
        with open(LOG_PATH, "r") as f:
            log_content = f.read()
            if "Successfully connected and authenticated" in log_content:
                bridge_status["authenticated"] = True
                return None
            elif "Scan this QR code" in log_content:
                # More aggressive QR code pattern matching
                qr_match = re.search(r"(█+[\s\S]*?QR code[\s\S]*?▀▀▀▀)", log_content, re.DOTALL)
                if qr_match:
                    bridge_status["qr_generated"] = True
                    return qr_match.group(1)
        return None
    except Exception as e:
        logger.error(f"Error extracting QR code: {e}")
        return None

@app.get("/qr")
def get_qr_status():
    # Update the last log check time
    bridge_status["last_log_check"] = time.time()
    
    try:
        # Check if the WhatsApp bridge is authenticated
        if bridge_status["authenticated"]:
            return {"status": "authenticated", "message": "WhatsApp is authenticated"}
            
        # Extract QR code if available
        qr_code = get_qr_from_logs()
        if qr_code:
            return {
                "status": "qr_ready", 
                "message": "QR code is ready to scan", 
                "qr": qr_code,
                "time_since_start": f"{int(time.time() - bridge_status['start_time'])}s"
            }
            
        # Check if enough time has passed since startup
        time_since_start = time.time() - bridge_status["start_time"]
    except Exception as e:
        logger.error(f"Error in get_qr_status: {e}")
        return {"status": "error", "message": f"Error getting QR status: {str(e)}"}
        
        # Check if the bridge is running using process check
        try:
            # Adjust for Windows vs Linux
            if os.name == 'nt':  # Windows
                result = subprocess.run(["tasklist"], capture_output=True, text=True)
                process_running = "main.exe" in result.stdout or "go.exe" in result.stdout
            else:  # Unix-like
                result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
                process_running = "main.go" in result.stdout
                
            if process_running:
                # Bridge is running but no QR code yet
                if time_since_start > 60:  # If more than 60 seconds
                    # Bridge is taking too long, offer to restart
                    return {
                        "status": "delayed", 
                        "message": f"WhatsApp bridge is running but QR code generation is taking longer than expected ({int(time_since_start)}s). You may want to restart.",
                        "restart_url": "/restart"
                    }
                else:
                    # Normal startup delay
                    return {
                        "status": "starting", 
                        "message": f"WhatsApp bridge is starting, waiting for QR code (running for {int(time_since_start)}s)"
                    }
            else:
                # Bridge not running, restart it
                if os.name == 'nt':  # Windows
                    # Windows-specific start command with PowerShell
                    cmd = f'cd "{BRIDGE_PATH}" && go run main.go -store ./store > "{LOG_PATH}" 2>&1'
                    subprocess.Popen(["powershell", "-Command", cmd], 
                                    creationflags=subprocess.CREATE_NEW_CONSOLE)
                else:  # Unix-like
                    # Linux-specific start command with bash
                    subprocess.Popen(["bash", "-c", f"cd {BRIDGE_PATH} && go run main.go -store ./store 2>&1 | tee {LOG_PATH} &"])
                
                return {
                    "status": "restarting", 
                    "message": "WhatsApp bridge was not running, attempting to restart"
                }
        except Exception as e:
            # Error checking process status
            logger.error(f"Error checking process status: {str(e)}")
            return {
                "status": "error",
                "message": f"Error checking WhatsApp bridge status: {str(e)}"
            }
            
@app.get("/logs")
def get_logs():
    """Endpoint to get the latest logs from the WhatsApp bridge"""
    try:
        if os.path.exists(LOG_PATH):
            with open(LOG_PATH, "r") as f:
                log_content = f.read()
                lines = log_content.splitlines()
                # Return the latest 100 lines to avoid overwhelming response
                return {"logs": "\n".join(lines[-100:])}
        return {"logs": "No logs found yet"}
    except FileNotFoundError:
        return {"logs": "No logs found yet"}
    except Exception as e:
        return {"logs": f"Error reading logs: {str(e)}"}

@app.get("/restart")
def restart_bridge():
    """Endpoint to restart the WhatsApp bridge"""
    try:
        # Kill existing bridge processes
        if os.name == 'nt':  # Windows
            os.system('taskkill /f /im go.exe 2>nul')
        else:  # Unix-like
            os.system("pkill -f 'go run main.go' 2>/dev/null || true")
            
        # Remove the log file to start fresh
        if os.path.exists(LOG_PATH):
            os.remove(LOG_PATH)
            
        # Start a new bridge process
        if os.name == 'nt':  # Windows
            cmd = f'cd "{BRIDGE_PATH}" && go run main.go -store ./store > "{LOG_PATH}" 2>&1'
            subprocess.Popen(["powershell", "-Command", cmd], 
                            creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:  # Unix-like
            subprocess.Popen(["bash", "-c", f"cd {BRIDGE_PATH} && go run main.go -store ./store 2>&1 | tee {LOG_PATH} &"])
            
        # Reset status flags
        bridge_status["authenticated"] = False
        bridge_status["qr_generated"] = False
        bridge_status["start_time"] = time.time()
        
        return {"status": "restarting", "message": "WhatsApp bridge is restarting"}
    except Exception as e:
        return {"status": "error", "message": f"Error restarting bridge: {str(e)}"}

# Create a direct HTTP client for the WhatsApp bridge API
whatsapp_client = httpx.AsyncClient(base_url="http://localhost:8080/api")

# Direct proxies for the MCP API
@app.post("/tool/{tool_name}")
async def proxy_tool(tool_name: str, request: Request):
    logger.info(f"MCP API request received for tool: {tool_name}")
    try:
        # Get the request body
        body = await request.json()
        logger.info(f"Request body: {body}")
        
        # Check if bridge is authenticated
        if not bridge_status["authenticated"]:
            # Check once more by parsing logs
            get_qr_from_logs()
            if not bridge_status["authenticated"]:
                return {
                    "success": False, 
                    "message": "WhatsApp bridge is not authenticated. Please scan the QR code at /qr endpoint."
                }
        
        # Handle send_message directly
        if tool_name == "send_message":
            recipient = body.get("recipient", "")
            message = body.get("message", "")
            logger.info(f"Sending message to {recipient}: {message}")
            
            if not recipient or not message:
                return {"success": False, "message": "Recipient and message are required"}
            
            try:
                # Make a direct HTTP request to the WhatsApp bridge API
                response = await whatsapp_client.post(
                    "/send",  # Changed from "/message/text" to "/send" to match WhatsApp bridge API
                    json={
                        "recipient": recipient,  # Use the recipient directly as the WhatsApp bridge expects
                        "message": message
                    }
                )
                
                result = response.json()
                logger.info(f"WhatsApp API response: {result}")
                
                # Format the response to match the expected MCP format
                success = response.status_code == 200 and result.get("success", False)
                status_message = result.get("message", "Unknown response")
                
                response_data = {"success": success, "message": status_message}
                logger.info(f"Send message response: {response_data}")
                return response_data
            except Exception as e:
                error_msg = f"Error sending message: {str(e)}"
                logger.error(error_msg)
                return {"success": False, "message": error_msg}
        
        # Handle other tools here as needed
        elif tool_name == "search_contacts":
            query = body.get("query", "")
            try:
                response = await whatsapp_client.get(f"/contacts/search?query={query}")
                return response.json()
            except Exception as e:
                return {"success": False, "message": f"Error searching contacts: {str(e)}"}
        
        # Default fallback response
        return {"success": False, "message": f"Tool {tool_name} implementation not found"}
    except Exception as e:
        error_msg = f"Error processing request: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "message": error_msg}

# Additional endpoints for n8n compatibility
@app.post("/api/tool/{tool_name}")
async def api_tool_proxy(tool_name: str, request: Request):
    """Alternate endpoint path for n8n compatibility"""
    # Simply forward to the main tool proxy handler
    return await proxy_tool(tool_name, request)

@app.post("/mcp/tool/{tool_name}")
async def mcp_tool_proxy(tool_name: str, request: Request):
    """Alternate endpoint path for MCP standard compatibility"""
    # Simply forward to the main tool proxy handler
    return await proxy_tool(tool_name, request)

def run_whatsapp_bridge():
    logger.info("Starting WhatsApp bridge...")
    try:
        # Ensure clean start
        if os.path.exists(LOG_PATH):
            os.remove(LOG_PATH)
            
        # Run with explicit store path to ensure persistence
        if os.name == 'nt':  # Windows
            store_path = os.path.join(BRIDGE_PATH, "store")
            os.makedirs(store_path, exist_ok=True)
            # Use PowerShell for Windows
            cmd = f'cd "{BRIDGE_PATH}" && go run main.go -store ./store > "{LOG_PATH}" 2>&1'
            subprocess.Popen(["powershell", "-Command", cmd], 
                             creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:  # Unix-like
            os.system(f"cd {BRIDGE_PATH} && go run main.go -store ./store 2>&1 | tee {LOG_PATH}")
    except Exception as e:
        logger.error(f"Error running WhatsApp bridge: {str(e)}")

# Background tasks to monitor and update status
def status_monitor():
    """Periodically check logs for status updates"""
    while True:
        try:
            # Check for QR code or authentication status 
            get_qr_from_logs()
            # Sleep for a bit
            time.sleep(5)
        except Exception as e:
            logger.error(f"Error in status monitor: {str(e)}")
            time.sleep(10)

# Start WhatsApp bridge in a separate thread
bridge_thread = threading.Thread(target=run_whatsapp_bridge)
bridge_thread.daemon = True
bridge_thread.start()

# Start the status monitor
monitor_thread = threading.Thread(target=status_monitor)
monitor_thread.daemon = True
monitor_thread.start()

if __name__ == "__main__":
    # Mark services as started
    bridge_status["started"] = True
    
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting API proxy server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)