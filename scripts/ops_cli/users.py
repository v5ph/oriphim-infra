#!/usr/bin/env python3
"""
User management CLI wrapper - calls /v1/onboarding/tenants/{tenant_id}/users endpoints
"""
import sys
import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"

def create_user(tenant_id: str, email: str, role: str, api_key: Optional[str] = None) -> int:
    """Create new user"""
    try:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "email": email,
            "role": role
        }
        
        response = requests.post(
            f"{BASE_URL}/v1/onboarding/tenants/{tenant_id}/users",
            headers=headers,
            json=payload,
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            print("✓ User created")
            print(json.dumps(data, indent=2))
            return 0
        else:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return 1
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return 2

def list_users(tenant_id: str, api_key: Optional[str] = None) -> int:
    """List users for tenant"""
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        response = requests.get(
            f"{BASE_URL}/v1/onboarding/tenants/{tenant_id}/users",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
            return 0
        else:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return 1
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return 2

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python users.py <command> [args]")
        print("Commands:")
        print("  create <tenant_id> <email> <role> [api_key]")
        print("  list <tenant_id> [api_key]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "create":
        if len(sys.argv) < 5:
            print("Error: tenant_id, email, and role required")
            sys.exit(1)
        tenant_id = sys.argv[2]
        email = sys.argv[3]
        role = sys.argv[4]
        api_key = sys.argv[5] if len(sys.argv) > 5 else None
        sys.exit(create_user(tenant_id, email, role, api_key))
    elif command == "list":
        if len(sys.argv) < 3:
            print("Error: tenant_id required")
            sys.exit(1)
        tenant_id = sys.argv[2]
        api_key = sys.argv[3] if len(sys.argv) > 3 else None
        sys.exit(list_users(tenant_id, api_key))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
