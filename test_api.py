#!/usr/bin/env python3
"""
WhatsApp MCP API Test Script
This script tests the various API endpoints for the WhatsApp MCP server.
"""

import requests
import json
import time
import sys

# Set this to your Render deployment URL or localhost for testing
BASE_URL = "https://whatsapp-mcp-n8n.onrender.com"  # Change to your actual URL
TEST_PHONE = "94712554352"  # Change this to your test phone number
TEST_MESSAGE = "Test message from API check script"

def test_status_endpoint():
    """Test the main status endpoint"""
    print("\n🔍 Testing Status Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Status endpoint is working!")
            return True
        else:
            print("❌ Status endpoint returned an error code.")
            return False
    except Exception as e:
        print(f"❌ Error accessing status endpoint: {str(e)}")
        return False

def test_qr_endpoint():
    """Test the QR code endpoint"""
    print("\n🔍 Testing QR Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/qr")
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Status: {data.get('status')}")
        print(f"Message: {data.get('message')}")
        
        # Don't print the QR code - it's too large
        if 'qr' in data:
            print("QR code is available for scanning")
        
        if response.status_code == 200:
            print("✅ QR endpoint is working!")
            return data.get('status') == 'authenticated'
        else:
            print("❌ QR endpoint returned an error code.")
            return False
    except Exception as e:
        print(f"❌ Error accessing QR endpoint: {str(e)}")
        return False

def test_send_message(endpoint_path="/tool/send_message"):
    """Test sending a WhatsApp message via the API"""
    print(f"\n🔍 Testing Send Message API ({endpoint_path})...")
    try:
        payload = {
            "recipient": TEST_PHONE,
            "message": f"{TEST_MESSAGE} via {endpoint_path} at {time.strftime('%H:%M:%S')}"
        }
        
        print(f"Sending payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            f"{BASE_URL}{endpoint_path}",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200 and response.json().get('success', False):
            print(f"✅ Message sent successfully via {endpoint_path}!")
            return True
        else:
            print(f"❌ Failed to send message via {endpoint_path}.")
            return False
    except Exception as e:
        print(f"❌ Error sending message: {str(e)}")
        return False

def main():
    """Main test function that tests all endpoints"""
    print("=" * 60)
    print("WhatsApp MCP API Test Script")
    print("=" * 60)
    print(f"Testing API endpoints at: {BASE_URL}")
    
    # Test status endpoint
    status_ok = test_status_endpoint()
    
    # Test QR endpoint and check if authenticated
    is_authenticated = test_qr_endpoint()
    
    if not is_authenticated:
        print("\n⚠️ WhatsApp is not authenticated. Please scan the QR code.")
        print(f"Visit {BASE_URL}/qr in your browser to see the QR code.")
        print("Once authenticated, re-run this script to test message sending.")
        return
    
    # Test all possible send message endpoints
    endpoints = [
        "/tool/send_message",
        "/api/tool/send_message",
        "/mcp/tool/send_message"
    ]
    
    success_count = 0
    for endpoint in endpoints:
        if test_send_message(endpoint):
            success_count += 1
    
    print("\n" + "=" * 60)
    if success_count == len(endpoints):
        print(f"✅ All {success_count} message endpoints are working correctly!")
    else:
        print(f"⚠️ {success_count} out of {len(endpoints)} message endpoints are working.")
        
    print("Test complete!")

if __name__ == "__main__":
    main()