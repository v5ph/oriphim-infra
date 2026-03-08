#!/usr/bin/env python3
"""
Tenant management CLI wrapper - calls /v1/onboarding/tenants endpoints
"""
import sys
import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"

def create_tenant(name: str, domain: str, tier: str = "standard", api_key: Optional[str] = None) -> int:
    """Create new tenant"""
    try:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "org_name": name,
            "domain": domain,
            "support_tier": tier
        }
        
        response = requests.post(
            f"{BASE_URL}/v1/onboarding/tenants",
            headers=headers,
            json=payload,
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            print("✓ Tenant created")
            print(json.dumps(data, indent=2))
            return 0
        else:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return 1
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return 2

def list_tenants(api_key: Optional[str] = None) -> int:
    """List all tenants"""
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        response = requests.get(f"{BASE_URL}/v1/onboarding/tenants", headers=headers, timeout=5)
        
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
        print("Usage: python tenants.py <command> [args]")
        print("Commands:")
        print("  create <name> <domain> [tier] [api_key]")
        print("  list [api_key]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "create":
        if len(sys.argv) < 4:
            print("Error: name and domain required")
            sys.exit(1)
        name = sys.argv[2]
        domain = sys.argv[3]
        tier = sys.argv[4] if len(sys.argv) > 4 else "standard"
        api_key = sys.argv[5] if len(sys.argv) > 5 else None
        sys.exit(create_tenant(name, domain, tier, api_key))
    elif command == "list":
        api_key = sys.argv[2] if len(sys.argv) > 2 else None
        sys.exit(list_tenants(api_key))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
