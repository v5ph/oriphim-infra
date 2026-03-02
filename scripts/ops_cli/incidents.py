#!/usr/bin/env python3
"""
Incident management CLI wrapper - calls /ops/incidents/* endpoints
"""
import sys
import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"

def list_incidents(api_key: Optional[str] = None) -> int:
    """List active incidents"""
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        response = requests.get(f"{BASE_URL}/ops/incidents", headers=headers, timeout=5)
        
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

def create_incident(severity: str, description: str, api_key: Optional[str] = None) -> int:
    """Create new incident"""
    try:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "severity": severity,
            "description": description
        }
        
        response = requests.post(
            f"{BASE_URL}/ops/incidents",
            headers=headers,
            json=payload,
            timeout=5
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            print("✓ Incident created")
            print(json.dumps(data, indent=2))
            return 0
        else:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return 1
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return 2

def resolve_incident(incident_id: str, api_key: Optional[str] = None) -> int:
    """Resolve incident"""
    try:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        response = requests.patch(
            f"{BASE_URL}/ops/incidents/{incident_id}/resolve",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Incident {incident_id} resolved")
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
        print("Usage: python incidents.py <command> [args]")
        print("Commands:")
        print("  list [api_key]")
        print("  create <severity> <description> [api_key]")
        print("  resolve <incident_id> [api_key]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        api_key = sys.argv[2] if len(sys.argv) > 2 else None
        sys.exit(list_incidents(api_key))
    elif command == "create":
        if len(sys.argv) < 4:
            print("Error: severity and description required")
            sys.exit(1)
        severity = sys.argv[2]
        description = sys.argv[3]
        api_key = sys.argv[4] if len(sys.argv) > 4 else None
        sys.exit(create_incident(severity, description, api_key))
    elif command == "resolve":
        if len(sys.argv) < 3:
            print("Error: incident_id required")
            sys.exit(1)
        incident_id = sys.argv[2]
        api_key = sys.argv[3] if len(sys.argv) > 3 else None
        sys.exit(resolve_incident(incident_id, api_key))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
