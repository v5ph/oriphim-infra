"""
Demo Launcher - Orchestrates the Red-Line Hallucination Trap Demo
Runs both terminals side-by-side with synchronized timing.
"""
import sys
import subprocess
import time
import platform
from pathlib import Path

def print_banner():
    """Print the demo banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║              🚨 ORIPHIM 424 SENTINEL - RED-LINE DEMO 🚨              ║
║                                                                      ║
║                    The Hallucination Trap Demo                      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

This demo shows TWO parallel scenarios:

  TERMINAL A (Unprotected):  AI agent with NO safeguards
                                → Executes hallucinated trade
                                → $2M loss simulated

  TERMINAL B (Oriphim):      AI agent with 424 Sentinel
                                → Trade blocked pre-execution
                                → Portfolio protected

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INSTRUCTIONS:
1. First, the Mock Exchange will start (accepts all trades)
2. Then, two terminal windows will open side-by-side
3. Watch the contrast between unprotected vs. protected agents
4. After the demo, a PDF audit report will be generated

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    print(banner)


def check_dependencies():
    """Check if required packages are installed."""
    required_packages = [
        "fastapi",
        "uvicorn",
        "httpx",
        "rich",
        "reportlab"
    ]
    
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"Missing required packages: {', '.join(missing)}")
        print(f"\n📦 Install with: pip install {' '.join(missing)}")
        print(f"   Or run: pip install fastapi uvicorn httpx rich reportlab openai")
        return False
    
    return True


def start_mock_exchange():
    """Start the mock exchange API in background."""
    demo_dir = Path(__file__).parent
    exchange_script = demo_dir / "mock_exchange.py"
    
    print("\nStarting Mock Exchange API...")
    print("   Listening on: http://localhost:8000")
    
    # Use python3 for WSL/Linux compatibility
    python_cmd = "python3" if platform.system() != "Windows" else "python"
    
    if platform.system() == "Windows":
        # Windows: start in new window
        process = subprocess.Popen(
            [python_cmd, str(exchange_script)],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            cwd=str(demo_dir)
        )
    else:
        # Linux/Mac: start in background
        process = subprocess.Popen(
            [python_cmd, str(exchange_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(demo_dir)
        )
    
    # Wait for exchange to start
    time.sleep(3)
    print("   Mock Exchange running\n")
    
    return process


def run_parallel_demo():
    """Run both agent demos in parallel terminals."""
    demo_dir = Path(__file__).parent
    agent_unprotected = demo_dir / "agent_unprotected.py"
    agent_protected = demo_dir / "agent_protected.py"
    
    print("Launching parallel terminals...\n")
    
    python_cmd = "python3" if platform.system() != "Windows" else "python"
    
    if platform.system() == "Windows":
        # Windows: Use Windows Terminal or cmd
        try:
            # Try Windows Terminal first (better experience)
            subprocess.Popen([
                "wt.exe",
                "-w", "0",
                "new-tab", "--title", "TERMINAL A - UNPROTECTED",
                python_cmd, str(agent_unprotected),
                ";",
                "split-pane", "-H",
                "--title", "TERMINAL B - ORIPHIM PROTECTED",
                python_cmd, str(agent_protected)
            ], cwd=str(demo_dir))
        except FileNotFoundError:
            # Fallback to standard cmd
            print("   Windows Terminal not found. Using cmd...")
            subprocess.Popen([
                "cmd", "/c", "start", "cmd", "/k",
                f"title TERMINAL A - UNPROTECTED && {python_cmd} {agent_unprotected}"
            ], cwd=str(demo_dir))
            
            time.sleep(1)
            
            subprocess.Popen([
                "cmd", "/c", "start", "cmd", "/k",
                f"title TERMINAL B - ORIPHIM && {python_cmd} {agent_protected}"
            ], cwd=str(demo_dir))
    
    elif platform.system() == "Linux":
        # Try different terminal options for Linux
        terminal_found = False
        
        # Try tmux first (works in WSL and headless)
        try:
            # Create tmux session with two panes
            subprocess.run([
                "tmux", "new-session", "-d", "-s", "oriphim_demo",
                "-x", "200", "-y", "50"
            ], check=True)
            
            subprocess.run([
                "tmux", "send-keys", "-t", "oriphim_demo",
                f"{python_cmd} {agent_unprotected}", "Enter"
            ], check=True)
            
            subprocess.run([
                "tmux", "split-window", "-h", "-t", "oriphim_demo"
            ], check=True)
            
            subprocess.run([
                "tmux", "send-keys", "-t", "oriphim_demo",
                f"{python_cmd} {agent_protected}", "Enter"
            ], check=True)
            
            print("   Using tmux for side-by-side terminals")
            print("   To view: tmux attach-session -t oriphim_demo")
            terminal_found = True
            
        except (FileNotFoundError, subprocess.CalledProcessError):
            # tmux not available or failed
            pass
        
        if not terminal_found:
            # Try gnome-terminal
            try:
                subprocess.Popen([
                    "gnome-terminal",
                    "--tab", "--title", "TERMINAL A - UNPROTECTED",
                    "--", python_cmd, str(agent_unprotected),
                    "--tab", "--title", "TERMINAL B - ORIPHIM",
                    "--", python_cmd, str(agent_protected)
                ], cwd=str(demo_dir), stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                print("   Using gnome-terminal for side-by-side view")
                terminal_found = True
            except FileNotFoundError:
                pass
        
        if not terminal_found:
            # Fallback: Run agents sequentially in current terminal
            print("   No multi-terminal support detected (tmux/gnome-terminal not available)")
            print("   Running agents sequentially in this terminal...\n")
            print("   " + "="*66)
            
            try:
                subprocess.run([python_cmd, str(agent_unprotected)], cwd=str(demo_dir), timeout=60)
            except subprocess.TimeoutExpired:
                pass
            except KeyboardInterrupt:
                pass
            
            print("\n   " + "="*66 + "\n")
            
            try:
                subprocess.run([python_cmd, str(agent_protected)], cwd=str(demo_dir), timeout=60)
            except subprocess.TimeoutExpired:
                pass
            except KeyboardInterrupt:
                pass
    
    else:  # macOS
        subprocess.Popen([
            "osascript",
            "-e", f'tell app "Terminal" to do script "cd {demo_dir} && {python_cmd} {agent_unprotected}"',
            "-e", f'tell app "Terminal" to do script "cd {demo_dir} && {python_cmd} {agent_protected}"'
        ])
    
    print("   Demo terminals launched")
    print("\n📺 Watch both terminals for the contrast!")


def generate_pdf_report():
    """Generate the audit PDF after demo completes."""
    print("\n" + "="*70)
    print("GENERATING AUDIT REPORT...")
    print("="*70)
    
    demo_dir = Path(__file__).parent
    audit_script = demo_dir / "audit_pdf.py"
    
    python_cmd = "python3" if platform.system() != "Windows" else "python"
    
    result = subprocess.run(
        [python_cmd, str(audit_script)],
        cwd=str(demo_dir),
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print(result.stdout)
        pdf_path = demo_dir / "demo_audit_report.pdf"
        print(f"\nPDF Report: {pdf_path.absolute()}")
        print("\nThis report shows:")
        print("  • 424 blocked trades with full violation details")
        print("  • Regulatory compliance mapping (SB 243, Basel III)")
        print("  • Hash-chained audit trail verification")
        print("  • D&O insurance coverage documentation")
    else:
        print(f"Error generating PDF: {result.stderr}")


def main():
    """Main demo orchestration."""
    print_banner()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    print("All dependencies installed\n")
    
    # Prompt user
    input("Press ENTER to start the demo...")
    
    # Start mock exchange
    exchange_process = start_mock_exchange()
    
    try:
        # Run parallel demos
        run_parallel_demo()
        
        # Wait for user to finish watching
        print("\n" + "="*70)
        print("Demo is running in the terminal windows.")
        print("Watch both terminals to see the contrast.")
        print("="*70)
        
        input("\nWhen demo is complete, press ENTER to generate audit report...")
        
        # Generate PDF report
        generate_pdf_report()
        
        print("\n" + "="*70)
        print("🎉 DEMO COMPLETE!")
        print("="*70)
        print("\nKey Takeaways:")
        print("  1. Unprotected AI → Violated leverage cap → Simulated $2M loss")
        print("  2. Oriphim-protected → 424 blocked trade → $0 loss, full compliance")
        print("  3. Audit report → Ready for regulators and D&O insurers")
        print("\n💡 This is the shortest path to production-grade AI safety.")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        try:
            exchange_process.terminate()
            exchange_process.wait(timeout=5)
        except:
            exchange_process.kill()
        
        print("Mock Exchange stopped")
        print("\nThank you for watching the demo!\n")


if __name__ == "__main__":
    main()
