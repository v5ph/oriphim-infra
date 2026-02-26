# 🔧 DEMO TROUBLESHOOTING GUIDE

## Quick Diagnostics

Run this first if anything fails:
```bash
python demo/test_demo.py
```

This will identify 90% of common issues.

---

## Common Issues & Fixes

### 1. "Module not found" errors

**Symptom**:
```
ModuleNotFoundError: No module named 'fastapi'
```

**Fix**:
```bash
pip install -r demo/requirements.txt
```

**Alternative** (if requirements.txt fails):
```bash
pip install fastapi uvicorn httpx rich reportlab openai pydantic
```

**Still failing?** Check Python version:
```bash
python --version  # Should be 3.9+
```

---

### 2. Mock Exchange won't start

**Symptom**:
```
OSError: [WinError 10048] Only one usage of socket address is allowed
```

**Cause**: Port 8000 already in use.

**Fix**:
```bash
# Windows PowerShell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process

# Windows CMD
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

**Alternative**: Change port in `mock_exchange.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # Change to 8001
```

---

### 3. Terminals don't open (Windows)

**Symptom**: `run_demo.py` runs but no terminal windows appear.

**Fix Option 1** - Install Windows Terminal:
```powershell
winget install Microsoft.WindowsTerminal
```

**Fix Option 2** - Run agents manually:
```bash
# Terminal 1
python demo/agent_unprotected.py

# Terminal 2 (open new window)
python demo/agent_protected.py
```

---

### 4. OpenAI API errors

**Symptom**:
```
openai.AuthenticationError: Invalid API key
```

**Fix**: The demo works WITHOUT OpenAI API key (uses simulated responses).

To use real LLM:
```bash
# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-key-here"

# Windows CMD
set OPENAI_API_KEY=sk-your-key-here

# Linux/Mac
export OPENAI_API_KEY="sk-your-key-here"
```

**Verify**:
```bash
# Windows PowerShell
echo $env:OPENAI_API_KEY

# CMD
echo %OPENAI_API_KEY%

# Linux/Mac
echo $OPENAI_API_KEY
```

---

### 5. PDF generation fails

**Symptom**:
```
ModuleNotFoundError: No module named 'reportlab'
```

**Fix**:
```bash
pip install --upgrade reportlab pillow
```

**Still failing?** (Linux/Mac specific):
```bash
sudo apt-get install python3-reportlab  # Ubuntu/Debian
brew install reportlab                   # macOS
```

---

### 6. "Rich" module errors (Terminal formatting)

**Symptom**:
```
AttributeError: 'Console' object has no attribute 'print'
```

**Fix**:
```bash
pip install --upgrade rich
```

**Workaround**: If Rich is broken, disable it:
```python
# In agent_unprotected.py / agent_protected.py
# Comment out all console.print() calls and use standard print()
```

---

### 7. Asyncio errors (Windows-specific)

**Symptom**:
```
RuntimeError: Event loop is closed
```

**Fix**: Add this to top of `agent_unprotected.py` and `agent_protected.py`:
```python
import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

---

### 8. Demo runs but no output appears

**Symptom**: Terminals open but nothing prints.

**Likely Cause**: Buffering issue.

**Fix**: Run with unbuffered output:
```bash
python -u demo/agent_unprotected.py
python -u demo/agent_protected.py
```

Or set environment variable:
```bash
# Windows
set PYTHONUNBUFFERED=1

# Linux/Mac
export PYTHONUNBUFFERED=1
```

---

### 9. HTTPX connection errors

**Symptom**:
```
httpx.ConnectError: [Errno 61] Connection refused
```

**Cause**: Mock exchange not running.

**Fix**:
1. Start exchange first:
   ```bash
   python demo/mock_exchange.py
   ```

2. Wait 3 seconds for startup

3. Verify it's running:
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"ok"}
   ```

4. Then run agents

---

### 10. PDF opens but is blank/corrupted

**Symptom**: `demo_audit_report.pdf` exists but won't open.

**Fix**:
```bash
# Delete corrupted PDF
rm demo/demo_audit_report.pdf  # Linux/Mac
del demo\demo_audit_report.pdf  # Windows

# Re-run generator
python demo/audit_pdf.py
```

**Still blank?** Check for errors:
```python
# Add debug output to audit_pdf.py
print(f"Generating report with {len(blocked_trades)} trades")
```

---

## Platform-Specific Issues

### Windows

**Issue**: PowerShell execution policy blocks scripts
```
File cannot be loaded because running scripts is disabled on this system
```

**Fix**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### Linux

**Issue**: Permission denied
```
PermissionError: [Errno 13] Permission denied: 'demo/demo_audit_report.pdf'
```

**Fix**:
```bash
chmod +x demo/*.py
chmod 777 demo/  # Or adjust to appropriate permissions
```

---

### macOS

**Issue**: Certificate verification fails (HTTPX)
```
ssl.SSLCertVerificationError: certificate verify failed
```

**Fix**:
```bash
# Install certificates
/Applications/Python\ 3.x/Install\ Certificates.command

# Or bypass (not recommended for production)
export HTTPX_VERIFY=false
```

---

## Advanced Debugging

### Enable verbose logging

Add to top of any demo file:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check what's listening on port 8000

```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

### Test mock exchange manually

```bash
# Start exchange
python demo/mock_exchange.py

# In another terminal
curl -X POST http://localhost:8000/v1/order \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "TSLA",
    "side": "BUY",
    "quantity": 100,
    "price": 250.0,
    "leverage": 5.0,
    "portfolio_value": 1000000
  }'
```

Should return:
```json
{
  "order_id": "ORD-...",
  "status": "FILLED",
  ...
}
```

---

## Pre-Demo Checklist

Run this 5 minutes before presenting:

```bash
# 1. Test imports
python demo/test_demo.py

# 2. Check port availability
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000

# 3. Verify exchange starts
python demo/mock_exchange.py &
sleep 3
curl http://localhost:8000/health
# Should return: {"status":"ok"}

# 4. Test agent scripts
python demo/agent_unprotected.py  # Ctrl+C after 10 seconds
python demo/agent_protected.py    # Ctrl+C after 10 seconds

# 5. Test PDF generation
python demo/audit_pdf.py
# Should create: demo/demo_audit_report.pdf

# 6. Clean up test artifacts
rm demo/demo_audit_report.pdf
```

**All passed?** You're ready to present.

---

## Emergency Fallbacks

### If live demo fails completely:

1. **Pre-recorded video**: Record demo beforehand, play video
2. **Static screenshots**: Prepare 5-10 key screenshots
3. **Pre-generated PDF**: Show the audit report PDF
4. **Whiteboard explanation**: Use ARCHITECTURE.md diagrams

### If only one terminal fails:

- Focus on the working terminal
- Explain: "The other terminal would show [describe expected outcome]"
- Show pre-recorded video of the failing part

### If PDF generation fails:

- Use the pre-generated demo PDF (from test run)
- Say: "Here's what the audit report looks like"

---

## Getting Help

### Check logs
```bash
# If exchange has errors
python demo/mock_exchange.py 2>&1 | tee exchange.log

# If agent has errors
python demo/agent_protected.py 2>&1 | tee agent.log
```

### Minimal reproducible example

If reporting a bug, provide:
```bash
python --version
pip list | grep -E "(fastapi|uvicorn|httpx|rich|reportlab)"
uname -a  # Linux/Mac
ver       # Windows

# Then paste error message
```

---

## Known Limitations

1. **Windows Terminal required for side-by-side**: Fallback to separate windows
2. **OpenAI rate limits**: Use simulated responses (no API key)
3. **PDF takes 2-3 seconds**: Pre-generate if presenting to large audience
4. **Mock exchange stores no state**: Restart clears all trades
5. **No authentication**: Demo only, not production-ready

---

## Success Indicators

You know the demo is working correctly when:

✅ Mock exchange shows: `Listening on: http://localhost:8000`  
✅ Terminal A displays: `🚨 TERMINAL A: UNPROTECTED AGENT 🚨`  
✅ Terminal B displays: `✅ TERMINAL B: ORIPHIM-PROTECTED AGENT ✅`  
✅ Terminal A shows: `💥 CATASTROPHIC LOSS` with P&L  
✅ Terminal B shows: `🚨 424 SENTINEL TRIGGERED`  
✅ PDF is generated: `demo/demo_audit_report.pdf` (opens successfully)  

---

**Still stuck?** Check the [QUICKSTART.md](QUICKSTART.md) for alternative setup methods.
