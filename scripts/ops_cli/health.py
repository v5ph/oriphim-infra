#!/usr/bin/env python3
"""
Health check CLI wrapper - calls /v2/health endpoint
"""
import sys
import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"

def health_check(api_key: Optional[str] = None) -> int:
    """Get system health status"""
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        response = requests.get(f"{BASE_URL}/v2/health", headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            indicator = data.get("indicator", "UNKNOWN")
            
            # Color coding
            if indicator == "GREEN":
                print(f"✓ System Health: {indicator}")
                print(json.dumps(data, indent=2))
                return 0
            elif indicator == "YELLOW":
                print(f"⚠ System Health: {indicator}")
                print(json.dumps(data, indent=2))
                return 1
            else:
                print(f"✗ System Health: {indicator}")
                print(json.dumps(data, indent=2))
                return 2
        else:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return 3
            
    except requests.exceptions.ConnectionError:
        print("✗ Connection failed - is the server running?")
        print("Try: uvicorn app.main:app --reload")
        return 4
    except Exception as e:
        print(f"✗ Error: {e}")
        return 5

if __name__ == "__main__":
    api_key = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(health_check(api_key))
