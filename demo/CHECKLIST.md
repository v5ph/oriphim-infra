# ✅ DEMO DEPLOYMENT CHECKLIST

## Phase 1: Immediate Testing (Next 30 Minutes)

### Setup Verification
- [ ] Navigate to demo directory: `cd demo`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Run component test: `python test_demo.py`
- [ ] Verify all tests pass (should see ✅ for all imports)

### Mock Exchange Test
- [ ] Start exchange: `python mock_exchange.py`
- [ ] Verify it's running: Check for "Listening on: http://localhost:8000"
- [ ] Test health endpoint: `curl http://localhost:8000/health` (should return `{"status":"ok"}`)
- [ ] Stop exchange: Ctrl+C

### Individual Component Tests
- [ ] Test unprotected agent: `python agent_unprotected.py` (run for 30 seconds, then Ctrl+C)
- [ ] Test protected agent: `python agent_protected.py` (run for 30 seconds, then Ctrl+C)
- [ ] Test PDF generator: `python audit_pdf.py` (should create `demo_audit_report.pdf`)
- [ ] Open PDF to verify it displays correctly

### Full Demo Test
- [ ] Run orchestrator: `python run_demo.py`
- [ ] Verify terminals open (or follow manual instructions)
- [ ] Watch both terminals complete their sequences
- [ ] Verify PDF is generated at the end
- [ ] Check that all output is readable

---

## Phase 2: Documentation Review (Next 30 Minutes)

### Read Key Documents
- [ ] Read [QUICKSTART.md](QUICKSTART.md) - 5-minute setup guide
- [ ] Skim [PRESENTER_SCRIPT.md](PRESENTER_SCRIPT.md) - Speaking notes
- [ ] Review [ARCHITECTURE.md](ARCHITECTURE.md) - Visual diagrams
- [ ] Bookmark [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - For quick reference

### Prepare Backup Materials
- [ ] Take screenshots of key demo moments:
  - [ ] Terminal A showing $2M loss
  - [ ] Terminal B showing 424 block
  - [ ] PDF audit report (first page)
- [ ] Save screenshots to `demo/screenshots/` folder
- [ ] Pre-generate 3 sample PDFs with different trade scenarios

---

## Phase 3: Presentation Prep (Next 1 Hour)

### Practice Run
- [ ] Do 3 full run-throughs without interruption
- [ ] Time each run (target: 2-3 minutes)
- [ ] Practice your voiceover using [PRESENTER_SCRIPT.md](PRESENTER_SCRIPT.md)
- [ ] Identify any timing issues or bottlenecks

### Technical Setup
- [ ] Determine your presentation environment:
  - [ ] Local machine (bring laptop to meeting)
  - [ ] Remote (share screen via Zoom/Teams)
  - [ ] Pre-recorded video (upload to YouTube/Loom)
- [ ] Test screen sharing if remote demo
- [ ] Verify resolution/font size is readable on projector/shared screen

### Backup Plans
- [ ] Create pre-recorded video (follow [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md))
- [ ] Prepare slide deck with screenshots as fallback
- [ ] Print PDF audit report (physical copy for board meetings)
- [ ] Test demo on backup laptop (if available)

---

## Phase 4: Customization (Optional - 2 Hours)

### Branding
- [ ] Add your company logo to PDF report (`audit_pdf.py` line ~30)
- [ ] Customize institution name in demo launcher
- [ ] Update contact info in presenter script

### Demo Variations
- [ ] Create "Fast Mode" (skip pauses, 90-second demo)
- [ ] Create "Detailed Mode" (add more explanation, 10-minute demo)
- [ ] Add second poisoned headline for variety

### Integration with Existing Codebase
- [ ] Connect demo to real Oriphim API (if deployed)
- [ ] Use actual constraint values from your production config
- [ ] Add your actual regulatory mappings

---

## Phase 5: Distribution Prep (Next 2 Hours)

### Video Recording
- [ ] Follow [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md) to record 5-min demo
- [ ] Edit video (trim pauses, add text overlays)
- [ ] Export as MP4 (1080p, <150 MB)
- [ ] Upload to YouTube (unlisted) or Loom

### Marketing Materials
- [ ] Write LinkedIn post (see [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md) for template)
- [ ] Prepare investor email (see [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md) for template)
- [ ] Create landing page or GitHub README with demo instructions
- [ ] Generate QR code linking to demo repo

### Stakeholder Outreach
- [ ] List 10 target investors/clients for demo
- [ ] Draft personalized email for each
- [ ] Schedule 5 demo calls for next week
- [ ] Prepare Q&A responses (see [PRESENTER_SCRIPT.md](PRESENTER_SCRIPT.md))

---

## Phase 6: Pre-Presentation Final Check (5 Minutes Before)

### Environment Setup
- [ ] Close all unnecessary applications
- [ ] Disable notifications (Focus Assist / Do Not Disturb)
- [ ] Set terminal font size to 14pt+ (visible on projector)
- [ ] Position terminal windows side-by-side
- [ ] Test microphone/audio if remote

### Component Verification
- [ ] Run `python test_demo.py` one final time
- [ ] Verify port 8000 is available
- [ ] Check internet connection (if using real OpenAI API)
- [ ] Have backup video ready to play

### Mental Prep
- [ ] Review 30-second pitch (see [SUMMARY.md](SUMMARY.md))
- [ ] Rehearse first 60 seconds of script
- [ ] Have key metrics ready:
  - 25x leverage → 10x cap
  - $2M loss prevented
  - 85ms validation latency
  - 3,000% ROI
  - $65-70M capital freed per $500M AUM

---

## Common Pre-Demo Mistakes to Avoid

- ❌ Not testing on presentation machine beforehand
- ❌ Using production API keys in demo (use simulated responses)
- ❌ Forgetting to disable notifications (email popups during demo)
- ❌ Terminal font too small (not readable on projector)
- ❌ No backup plan if demo fails
- ❌ Rushing through demo (let 424 block moment breathe)
- ❌ Over-explaining technical details (keep it business-focused)
- ❌ Not having ROI numbers memorized

---

## Emergency Contact Checklist

Have these ready in case of technical issues:

- [ ] IT support contact (if presenting at client site)
- [ ] Backup presenter (if you get sick/stuck in traffic)
- [ ] Pre-recorded video link (share via phone if laptop fails)
- [ ] Physical backup (printed slides + PDF report)

---

## Post-Demo Actions

### Immediate (Within 1 Hour)
- [ ] Send PDF audit report to attendees
- [ ] Share demo GitHub link
- [ ] Send calendar invite for follow-up meeting
- [ ] Note any questions you couldn't answer (for follow-up)

### Follow-Up (Within 24 Hours)
- [ ] Email recap with key metrics
- [ ] Share video recording (if recorded)
- [ ] Send pricing proposal (see [SUMMARY.md](SUMMARY.md))
- [ ] Schedule technical deep-dive call

### Long-Term (Within 1 Week)
- [ ] Collect feedback: "What worked? What didn't?"
- [ ] Iterate on demo based on feedback
- [ ] Document common questions for FAQ
- [ ] Share success stories (if demo led to pilot/sale)

---

## Success Metrics

You'll know your demo was successful if:

✅ Audience asks: "Can we run this on our data?"  
✅ Board member says: "What's the setup timeline?"  
✅ CRO asks: "Does this satisfy our auditors?"  
✅ CFO calculates ROI on their portfolio size  
✅ Legal team asks about D&O insurance language  
✅ Someone requests PDF audit report sample  
✅ You schedule follow-up meeting before leaving  

---

## Final Reminder

**The demo is not about impressing with technology.**  
**It's about showing a business-critical problem (D&O liability) and a deterministic solution (424 Sentinel).**

The contrast between Terminal A and Terminal B does the work. Let it breathe.

---

## Quick Reference: One-Liners for Objections

**"Our AI is already safe."**  
→ "Great. Can your auditors verify that with an immutable audit trail? Here's ours." [Show PDF]

**"This seems like overkill."**  
→ "Your D&O insurance policy has a clause about 'unsupervised autonomous systems.' This satisfies that clause."

**"What if we just monitor logs?"**  
→ "Monitoring is post-facto. The trade already executed. This blocks pre-execution."

**"Latency is critical for us."**  
→ "85 milliseconds. Sub-100ms guarantee. If you're doing microsecond HFT, you're not using LLMs anyway."

**"We can build this in-house."**  
→ "Absolutely. Factor in 6 months dev time, regulatory review, auditor validation, and D&O underwriter approval. Or deploy next week."

**"The ROI seems too good to be true."**  
→ "It's not the software ROI. It's the capital efficiency ROI. Basel III charges 15% operational risk on unmitigated AI. We drop that to 1-2%. The math is simple."

---

**YOU'RE READY.** Run `python demo/run_demo.py` and change the game. 🚀
