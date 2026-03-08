#!/usr/bin/env python3
"""
Bootstrap script to create a demo tenant, user, and API key for local development.

Usage:
    python scripts/setup/bootstrap_demo.py

This creates:
- Demo tenant: "Acme Corporation" (acme.com)
- Demo user: admin@acme.com (Admin role)
- Demo API key: Printed to console and saved to .demo_api_key file
"""

import os
import sys
from pathlib import Path

# Add parent directory to path so imports work
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.storage import init_db
from app.core.onboarding import (
    init_onboarding_db,
    create_tenant,
    create_user,
    generate_api_key,
)


def bootstrap():
    """Initialize database and create demo credentials."""
    print("Initializing Oriphim demo environment...")

    # Initialize databases
    print("  - Initializing storage database...")
    init_db()

    print("  - Initializing onboarding database...")
    init_onboarding_db()

    # Create demo tenant
    print("  - Creating demo tenant 'Acme Corporation'...")
    tenant = create_tenant(
        org_name="Acme Corporation",
        domain="acme.com",
        support_tier="standard"
    )
    tenant_id = tenant["tenant_id"]
    print(f"    Tenant ID: {tenant_id}")

    # Create demo user
    print("  - Creating demo user 'admin@acme.com'...")
    user = create_user(
        tenant_id=tenant_id,
        email="admin@acme.com",
        role="admin"
    )
    user_id = user["user_id"]
    print(f"    User ID: {user_id}")

    # Generate API key
    print("  - Generating API key...")
    key_data = generate_api_key(
        tenant_id=tenant_id,
        user_id=user_id,
        scope="admin",
        expires_in_days=90
    )
    api_key = key_data["api_key"]

    # Save to file for easy reference
    key_file = Path(__file__).resolve().parents[2] / ".demo_api_key"
    with open(key_file, "w") as f:
        f.write(api_key)
    key_file.chmod(0o600)

    print("\n" + "=" * 70)
    print("SUCCESS: Demo environment initialized!")
    print("=" * 70)
    print(f"\nDemo Credentials:")
    print(f"  Organization: Acme Corporation")
    print(f"  Tenant ID: {tenant_id}")
    print(f"  User Email: admin@acme.com")
    print(f"  API Key: {api_key}")
    print(f"\nAPI Key saved to: {key_file}")
    print("\nNext steps:")
    print("  1. Start the backend: uvicorn app.main:app --reload")
    print("  2. Start the dashboard: npm run dev (in client-dashboard/)")
    print("  3. Navigate to http://localhost:5173")
    print("  4. Login with the API key above")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    try:
        bootstrap()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
