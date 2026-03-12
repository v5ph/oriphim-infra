"""
Test API key fixture for automated testing.

Usage in tests:
    from tests.fixtures.test_api_key import get_test_api_key
    
    api_key = get_test_api_key()
"""

import os
from typing import Optional


def get_test_api_key() -> str:
    """
    Retrieve test API key from environment.
    
    Returns:
        str: Test API key from TEST_API_KEY env var
        
    Raises:
        RuntimeError: If TEST_API_KEY not set
        
    Security:
        - Never hardcoded
        - Only used in test environment
        - Must be explicitly set via environment
    """
    key = os.getenv("TEST_API_KEY")
    
    if not key:
        raise RuntimeError(
            "TEST_API_KEY environment variable not set.\n"
            "For local testing:\n"
            "  1. Run: python scripts/setup/bootstrap_demo.py\n"
            "  2. Export: export TEST_API_KEY=$(cat .demo_api_key)\n"
            "For CI/CD, set TEST_API_KEY in pipeline secrets."
        )
    
    return key


def get_test_api_key_optional() -> Optional[str]:
    """
    Retrieve test API key if available (non-failing variant).
    
    Returns:
        str | None: Test API key or None if not set
    """
    return os.getenv("TEST_API_KEY")
