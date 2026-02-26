"""
Quick test script - Verify demo components work before running full demo.
"""
import sys

def test_imports():
    """Test that all required packages can be imported."""
    print("Testing imports...")
    
    tests = {
        "FastAPI": lambda: __import__("fastapi"),
        "Uvicorn": lambda: __import__("uvicorn"),
        "HTTPX": lambda: __import__("httpx"),
        "Rich": lambda: __import__("rich"),
        "ReportLab": lambda: __import__("reportlab"),
        "OpenAI": lambda: __import__("openai"),
    }
    
    failed = []
    
    for name, test_func in tests.items():
        try:
            test_func()
            print(f"  OK: {name}")
        except ImportError:
            print(f"  FAILED: {name}")
            failed.append(name)
    
    if failed:
        print(f"\nFailed imports: {', '.join(failed)}")
        print("Run: pip install -r demo/requirements.txt")
        return False
    
    print("\nAll imports successful!")
    return True


def test_demo_components():
    """Test that demo components are loadable."""
    print("\nTesting demo components...")
    
    components = [
        ("Mock Exchange", "mock_exchange"),
        ("News Feed", "news_feed"),
        ("Rewind Service", "rewind_service"),
        ("Audit PDF", "audit_pdf"),
    ]
    
    failed = []
    
    for name, module in components:
        try:
            __import__(module)
            print(f"  OK: {name}")
        except Exception as e:
            print(f"  FAILED: {name}: {e}")
            failed.append(name)
    
    if failed:
        print(f"\nFailed components: {', '.join(failed)}")
        return False
    
    print("\nAll components loaded!")
    return True


def main():
    print("="*70)
    print("ORIPHIM DEMO - COMPONENT TEST")
    print("="*70)
    print()
    
    if not test_imports():
        sys.exit(1)
    
    if not test_demo_components():
        sys.exit(1)
    
    print("\n" + "="*70)
    print("ALL TESTS PASSED - READY TO RUN DEMO")
    print("="*70)
    print("\nRun the demo with: python demo/run_demo.py")
    print()


if __name__ == "__main__":
    main()
