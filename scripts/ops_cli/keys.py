#!/usr/bin/env python3
"""
API Key management CLI wrapper - calls /v1/onboarding/tenants/{tenant_id}/api-keys endpoints
"""
import sys
import requests
import json
from typing import Optional
import os

BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT_SECONDS = int(os.getenv("OPS_CLI_TIMEOUT_SECONDS", "20"))

def generate_key(tenant_id: str, user_id: str, scope: str = "viewer", api_key: Optional[str] = None) -> int:
    """Generate new API key"""
    try:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "user_id": user_id,
            "scope": scope
        }
        
        response = requests.post(
            f"{BASE_URL}/v1/onboarding/tenants/{tenant_id}/api-keys",
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            print("✓ API key generated")
            print(json.dumps(data, indent=2))
            print("\n⚠ SAVE THIS KEY - it won't be shown again!")
            return 0
        else:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return 1
            
    except requests.exceptions.Timeout:
        print(
            f"✗ Error: Request timed out after {REQUEST_TIMEOUT_SECONDS}s. "
            "Check API server status and retry."
        )
        return 2
    except Exception as e:
        print(f"✗ Error: {e}")
        return 2

def list_keys(tenant_id: str, api_key: Optional[str] = None) -> int:
    """List API keys for tenant"""
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        response = requests.get(
            f"{BASE_URL}/v1/onboarding/tenants/{tenant_id}/api-keys",
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS
        )
        
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
            return 0
        else:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return 1
            
    except requests.exceptions.Timeout:
        print(
            f"✗ Error: Request timed out after {REQUEST_TIMEOUT_SECONDS}s. "
            "Check API server status and retry."
        )
        return 2
    except Exception as e:
        print(f"✗ Error: {e}")
        return 2

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python keys.py <command> [args]")
        print("Commands:")
        print("  generate <tenant_id> <user_id> [scope] [api_key]")
        print("  list <tenant_id> [api_key]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "generate":
        if len(sys.argv) < 4:
            print("Error: tenant_id and user_id required")
            sys.exit(1)
        tenant_id = sys.argv[2]
        user_id = sys.argv[3]
        scope = sys.argv[4] if len(sys.argv) > 4 else "viewer"
        api_key = sys.argv[5] if len(sys.argv) > 5 else None
        sys.exit(generate_key(tenant_id, user_id, scope, api_key))
    elif command == "list":
        if len(sys.argv) < 3:
            print("Error: tenant_id required")
            sys.exit(1)
        tenant_id = sys.argv[2]
        api_key = sys.argv[3] if len(sys.argv) > 3 else None
        sys.exit(list_keys(tenant_id, api_key))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
