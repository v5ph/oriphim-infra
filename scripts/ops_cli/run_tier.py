#!/usr/bin/env python3
"""
Test execution CLI wrapper - calls /ops/tests/runs endpoint
"""
import sys
import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"

def run_tier(tier: int, api_key: Optional[str] = None) -> int:
    """Execute test tier"""
    try:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        payload = {
            "tier": tier,
            "environment": "staging"
        }
        
        response = requests.post(
            f"{BASE_URL}/ops/tests/runs",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"✓ Tier {tier} test initiated")
            print(json.dumps(data, indent=2))
            return 0
        else:
            print(f"Error: HTTP {response.status_code}")
            print(response.text)
            return 1
            
    except requests.exceptions.ConnectionError:
        print("✗ Connection failed - is the server running?")
        return 2
    except Exception as e:
        print(f"✗ Error: {e}")
        return 3

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_tier.py <tier> [api_key]")
        print("Example: python run_tier.py 1")
        sys.exit(1)
    
    tier = int(sys.argv[1])
    api_key = sys.argv[2] if len(sys.argv) > 2 else None
    sys.exit(run_tier(tier, api_key))
