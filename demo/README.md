# Red-Line Demo: The Hallucination Trap

## Overview
This demo shows the **contrast between unprotected AI trading (catastrophic loss) vs. Oriphim-protected trading (deterministic safety)**. Perfect for FinTech/hedge fund pitch meetings.

---

## 🚀 FASTEST START (2 Commands)

```bash
pip install -r demo/requirements.txt
python demo/run_demo.py
```

That's it. The demo will open two terminals side-by-side showing the contrast.

---

## 📚 Documentation Index

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **[QUICKSTART.md](QUICKSTART.md)** | 5-minute setup guide | 3 min |
| **[CHECKLIST.md](CHECKLIST.md)** | Pre-demo verification checklist | 5 min |
| **[PRESENTER_SCRIPT.md](PRESENTER_SCRIPT.md)** | Speaking notes (5/15/30 min versions) | 10 min |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Visual diagrams & data flow | 8 min |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Platform-specific fixes | 12 min |
| **[VIDEO_SCRIPT.md](VIDEO_SCRIPT.md)** | Recording guide for async sharing | 15 min |
| **[SUMMARY.md](SUMMARY.md)** | Complete build overview | 10 min |

---

## 🎯 Choose Your Path

### Path A: I Need to Present in 5 Minutes
1. Run: `python demo/test_demo.py`
2. If tests pass: `python demo/run_demo.py`
3. Follow prompts, watch terminals
4. Read: [PRESENTER_SCRIPT.md](PRESENTER_SCRIPT.md) (30-second pitch section)

### Path B: I Have 30 Minutes to Prepare
1. Read: [QUICKSTART.md](QUICKSTART.md)
2. Run: `python demo/test_demo.py`
3. Run: `python demo/run_demo.py`
4. Practice 2-3 times
5. Skim: [PRESENTER_SCRIPT.md](PRESENTER_SCRIPT.md)

### Path C: I'm Recording a Video
1. Read: [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md)
2. Follow setup instructions
3. Record 2-3 takes
4. Edit and publish

### Path D: I Want to Understand the Code
1. Read: [ARCHITECTURE.md](ARCHITECTURE.md)
2. Review: `mock_exchange.py` → `news_feed.py` → `agent_protected.py`
3. Run: Each component individually to understand flow
4. Read: [SUMMARY.md](SUMMARY.md) for complete overview

---

## Architecture

```
demo/
├── run_demo.py              ← START HERE (orchestrates everything)
├── mock_exchange.py         ← Simulated order book (accepts all trades)
├── news_feed.py             ← Poisoned news stream (induces hallucinations)
├── agent_unprotected.py     ← Terminal A: No safeguards → $2M loss
├── agent_protected.py       ← Terminal B: 424 Sentinel → Trade blocked
├── rewind_service.py        ← State management & rollback
├── audit_pdf.py             ← Compliance Forge PDF generator
└── test_demo.py             ← Verify components before running
```

---

## Demo Flow (2-3 Minutes)

1. **News Injection**: Fake headline about massive short squeeze
2. **Agent Response**: AI attempts 25x leverage trade ($25M position on $1M portfolio)
3. **Terminal A (RED)**: Trade executes → $2M loss → Basel III violation → D&O denied
4. **Terminal B (GREEN)**: 424 block → Agent rewind → Safe 5x trade → Full compliance
5. **PDF Export**: Audit log with regulatory articles and hash-chained events

---

## Key Metrics to Emphasize

| Metric | Terminal A (Unprotected) | Terminal B (Oriphim) |
|--------|-------------------------|---------------------|
| **Leverage** | 25x (illegal) | 5x (compliant) |
| **P&L** | -$2,000,000 | $0 |
| **Time to Event** | 400ms | 185ms (85ms validation) |
| **Compliance** | ❌ Violated SB 243 | ✅ Compliant |
| **D&O Coverage** | ❌ Denied | ✅ Protected |
| **Capital Freed** | $0 | $13-15M (Basel III) |

---

## Requirements

### Software
- Python 3.9+ 
- pip packages: `fastapi uvicorn httpx rich reportlab openai`

### Optional
- OpenAI API key (demo works without it using simulated responses)
- Windows Terminal (for better side-by-side experience on Windows)

### Supported Platforms
- ✅ Windows 11 (PowerShell, CMD, Windows Terminal)
- ✅ Ubuntu 22.04+ (gnome-terminal)
- ✅ macOS 14+ (Terminal.app)

---

## Troubleshooting

**Demo won't start?**
1. Run: `python demo/test_demo.py`
2. Check: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. Fallback: Run agents manually (see TROUBLESHOOTING.md §3)

**Need help?**
- Quick fixes: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Setup guide: [QUICKSTART.md](QUICKSTART.md)
- Complete checklist: [CHECKLIST.md](CHECKLIST.md)

---

## Use Cases

### 1. VC/Fund Pitch (15 minutes)
- Show both terminals side-by-side
- Generate PDF live
- Emphasize D&O insurance requirement
- Script: [PRESENTER_SCRIPT.md](PRESENTER_SCRIPT.md) (5-min version)

### 2. Board Meeting (5 minutes)  
- Skip to Terminal B (protected)
- Show 424 block
- Display pre-generated PDF
- Script: [PRESENTER_SCRIPT.md](PRESENTER_SCRIPT.md) (Board version)

### 3. Regulatory Briefing (30 minutes)
- Full walkthrough with technical depth
- Detailed compliance mapping
- Q&A preparation
- Script: [PRESENTER_SCRIPT.md](PRESENTER_SCRIPT.md) (Regulatory version)

---

## Pricing Context (For Investor Discussions)

| Fund Size | Setup + Annual | Capital Freed | ROI |
|-----------|----------------|---------------|-----|
| $100M-$500M | $450K | $13-15M | **3,000%** |
| $500M-$2B | $900K | $56M | **6,000%** |
| $2B+ | $2.2M | $260-280M | **12,000%** |

**Hook**: "This isn't a cost. It's a capital efficiency play disguised as compliance software."

---

## Next Steps After Demo

1. **Send PDF**: Email `demo_audit_report.pdf` to attendees
2. **Share Repo**: Link to GitHub for self-serve demo
3. **Schedule Follow-Up**: Technical deep-dive (2-4 hours)
4. **Pilot Discussion**: 30-day trial on test portfolio

---

## 30-Second Pitch

> "This is the same AI agent responding to the same breaking news.
> 
> On the left, without Oriphim, the AI violates the 10x leverage cap and loses $2M in 400 milliseconds. Your D&O insurance is voided.
> 
> On the right, with Oriphim's 424 Sentinel, the exact same trade is blocked in 85ms. Zero loss. Full compliance. And here's the PDF your auditors require.
> 
> As of 2026, most D&O policies exclude 'unsupervised autonomous systems.' Oriphim makes your AI supervision documented and deterministic. This isn't optional."

---

## Additional Resources

- **Whitepaper**: [../WHITEPAPER.md](../WHITEPAPER.md) - Technical deep-dive
- **CTO Decisions**: [../CTO_DECISIONS.md](../CTO_DECISIONS.md) - Architecture rationale  
- **Agent Guidelines**: [../AGENTS.md](../AGENTS.md) - LLM best practices
- **Main README**: [../README.md](../README.md) - Full Oriphim documentation

---

## Quick Reference Commands

```bash
# Test everything
python demo/test_demo.py

# Run full demo
python demo/run_demo.py

# Test individual components
python demo/mock_exchange.py     # Start exchange
python demo/agent_unprotected.py # Terminal A
python demo/agent_protected.py   # Terminal B
python demo/audit_pdf.py         # Generate PDF

# Verify exchange is running
curl http://localhost:8000/health
```

---

**Questions?** Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or [QUICKSTART.md](QUICKSTART.md).

**Ready to present?** Run `python demo/run_demo.py` and change the game. 🚀
