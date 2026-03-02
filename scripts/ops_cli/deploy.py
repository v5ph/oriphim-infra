#!/usr/bin/env python3
"""
Deployment CLI wrapper - calls /ops/deployments/* endpoints
"""
import sys
import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"

def deploy_canary(api_key: Optional[str] = None) -> int:
    """Initiate canary deployment"""
    try:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "version": "latest",
            "traffic_percentage": 10
        }
        
        response = requests.post(
            f"{BASE_URL}/ops/deployments/canary",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            print("✓ Canary deployment initiated")
            print(json.dumps(data, indent=2))
            return 0
        else:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return 1
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return 2

def deploy_status(deployment_id: Optional[str] = None, api_key: Optional[str] = None) -> int:
    """Get deployment status"""
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        url = f"{BASE_URL}/ops/deployments/status"
        if deployment_id:
            url += f"?deployment_id={deployment_id}"
        
        response = requests.get(url, headers=headers, timeout=5)
        
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

def deploy_rollback(deployment_id: str, api_key: Optional[str] = None) -> int:
    """Rollback deployment"""
    try:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        response = requests.post(
            f"{BASE_URL}/ops/deployments/{deployment_id}/rollback",
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✓ Rollback initiated for {deployment_id}")
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
        print("Usage: python deploy.py <command> [args]")
        print("Commands:")
        print("  canary [api_key]")
        print("  status [deployment_id] [api_key]")
        print("  rollback <deployment_id> [api_key]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "canary":
        api_key = sys.argv[2] if len(sys.argv) > 2 else None
        sys.exit(deploy_canary(api_key))
    elif command == "status":
        deployment_id = sys.argv[2] if len(sys.argv) > 2 else None
        api_key = sys.argv[3] if len(sys.argv) > 3 else None
        sys.exit(deploy_status(deployment_id, api_key))
    elif command == "rollback":
        if len(sys.argv) < 3:
            print("Error: deployment_id required for rollback")
            sys.exit(1)
        deployment_id = sys.argv[2]
        api_key = sys.argv[3] if len(sys.argv) > 3 else None
        sys.exit(deploy_rollback(deployment_id, api_key))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
