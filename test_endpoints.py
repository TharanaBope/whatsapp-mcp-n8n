import requests
import json

# Base URL of your Render service
base_url = "https://whatsapp-mcp-n8n.onrender.com"

# Different potential endpoint structures to test
endpoints = [
    "/tool/send_message",
    "/mcp/tool/send_message",
    "/api/tool/send_message",
    "/v1/tool/send_message"
]

# Test payload
payload = {
    "recipient": "REPLACE_WITH_PHONE_NUMBER",  # Replace with actual phone number
    "message": "Test message from API check script"
}

# Try each endpoint
for endpoint in endpoints:
    full_url = base_url + endpoint
    print(f"Testing endpoint: {full_url}")
    
    try:
        response = requests.post(
            full_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=10
        )
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code != 404:
            print(f"✅ SUCCESS: Endpoint {endpoint} returned non-404 response")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    
    print("-" * 50)