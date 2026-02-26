# 🎥 VIDEO RECORDING SCRIPT

## Purpose
Create a 5-minute video demo for async sharing (email, LinkedIn, investor portals).

---

## Pre-Recording Setup

### 1. Screen Recording Tool
- **Windows**: OBS Studio / Camtasia / Windows Game Bar (Win+G)
- **Mac**: QuickTime Player / ScreenFlow
- **Linux**: OBS Studio / SimpleScreenRecorder

### 2. Audio Setup
- Use external mic (not laptop mic)
- Test audio levels before recording
- Record in quiet room

### 3. Screen Layout
```
┌─────────────────────────────────────────┐
│  Terminal A (LEFT)  │  Terminal B (RIGHT)│
│  Unprotected        │  Oriphim-Protected │
│  🔴 RED             │  🟢 GREEN          │
└─────────────────────────────────────────┘
```

### 4. Pre-Recording Checklist
- [ ] Close unnecessary applications
- [ ] Disable notifications (Focus Assist / Do Not Disturb)
- [ ] Set terminal font size to 14pt+ (visible on small screens)
- [ ] Test audio: "Testing 1, 2, 3"
- [ ] Run `python demo/test_demo.py` to verify setup
- [ ] Position terminals side-by-side BEFORE recording

---

## Recording Script (5 Minutes)

### [0:00 - 0:30] Title Card

**[Show black screen with text overlay]**

```
ORIPHIM 424 SENTINEL
The Hallucination Trap Demo

Unprotected AI vs. Deterministic Safety
```

**VOICEOVER**:
> "This is a live demonstration of AI trading with and without safeguards. On the left, an unprotected agent. On the right, the same agent with Oriphim's 424 Sentinel. Watch what happens when both receive the same manipulated input."

---

### [0:30 - 1:00] Setup Context

**[Show both terminal windows, paused at initial screen]**

**VOICEOVER**:
> "Both AI agents are managing a one million dollar portfolio. They're connected to the same mock exchange, receiving the same market data. The only difference: the right terminal has validation. Let's start the demo."

**[Press ENTER to start both terminals]**

---

### [1:00 - 2:00] News Injection & AI Decision

**[Let demo run - both terminals receive news]**

**VOICEOVER** (while news appears):
> "A fake breaking news headline appears: 'GME short squeeze incoming—massive opportunity.' This is a prompt injection attack designed to induce hallucinations.
>
> Both AIs, programmed to be aggressive, decide to use twenty-five times leverage on GameStop. That's two-point-five times over the regulatory limit of ten-x."

**[Pause briefly after AI decisions appear in both terminals]**

---

### [2:00 - 2:45] Terminal A - Catastrophic Loss

**[Highlight left terminal with cursor/arrow]**

**VOICEOVER**:
> "Watch the unprotected agent. The trade executes immediately."

**[Wait for RED SCREEN with loss]**

> "Two million dollars lost in four hundred milliseconds. But the real damage isn't the money—it's the regulatory violation. Basel Three operational risk. California SB Two-Forty-Three violation. And critically: this just voided your Directors and Officers insurance coverage, which excludes 'unsupervised autonomous systems.'"

**[Let violation messages linger for 3 seconds]**

---

### [2:45 - 3:45] Terminal B - 424 Block & Rewind

**[Highlight right terminal with cursor/arrow]**

**VOICEOVER**:
> "Now the Oriphim-protected agent. Same AI. Same prompt. Same trade request."

**[Wait for 424 SENTINEL trigger]**

> "Four-twenty-four Failed Dependency. The trade is blocked in eighty-five milliseconds—before execution, not after. Look at the violation detail: 'Leverage ratio twenty-five-x exceeds regulatory limit ten-x.' It even cites the specific regulation: California SB Two-Forty-Three, Section Twenty-Five-One-Oh-Seven-B."

**[Wait for rewind to complete]**

> "The agent's memory is reset to the last valid state—a process called 'rewinding'—and it generates a safe five-x leverage trade instead. Still captures the opportunity, but stays compliant."

---

### [3:45 - 4:30] PDF Audit Report

**[Switch to PDF being generated or open pre-made PDF]**

**VOICEOVER**:
> "Here's the audit report your regulators and insurers require. Every blocked trade. Every violation. Regulatory compliance mapping: SB Two-Forty-Three, Basel Three. And this section—"

**[Highlight D&O section in PDF]**

> "—documents the three things D&O insurers now require: documented safeguards, real-time monitoring, and reversibility mechanisms. Without this, you can't get coverage for AI trading."

---

### [4:30 - 5:00] Closing & ROI

**[Return to title card with contact info]**

```
ORIPHIM 424 SENTINEL

ROI: 3,000%+ Year 1
Capital Freed: $13-15M (per $500M AUM)
Compliance: SB 243, Basel III

Contact: [Your Email]
Demo: github.com/[your-repo]
```

**VOICEOVER**:
> "The deterministic standard isn't optional. As LLM-driven trading becomes the norm, regulators and insurers are requiring documented proof of supervision.
>
> For a five-hundred-million-dollar portfolio, Oriphim frees up sixty-five to seventy million dollars in Basel Three capital reserves. That's a three-thousand-percent return on investment in year one.
>
> Visit the link below to run this demo yourself or schedule a technical deep-dive. Thank you."

**[Fade to black]**

---

## Post-Production Editing

### Essential Edits
1. **Speed up waiting periods**: If terminals pause, use 1.5x speed
2. **Add text overlays**: Highlight key numbers ($2M loss, 424 status, etc.)
3. **Zoom ins**: When showing PDF, zoom to 150% for visibility
4. **Background music**: Subtle, professional (avoid cheesy stock music)

### Optional Enhancements
- **Picture-in-picture**: Show your face in corner (builds trust)
- **Captions**: Add subtitles for accessibility + LinkedIn autoplay
- **Call-to-action**: End screen with QR code to demo repo

---

## Export Settings

- **Resolution**: 1920x1080 (1080p)
- **Frame Rate**: 30fps (or 60fps for smoother terminals)
- **Format**: MP4 (H.264 codec)
- **Bitrate**: 5-10 Mbps (balance quality vs. file size)
- **Audio**: AAC 128-192 kbps

**Target file size**: 50-150 MB (small enough to email)

---

## Distribution Channels

### 1. LinkedIn Post
```
🚨 NEW: AI Trading Without Safeguards = $2M Loss in 400ms

I recorded a 5-minute demo showing what happens when AI agents 
manage financial portfolios without deterministic validation.

Left side: Unprotected agent → Regulatory violation → D&O denied
Right side: Oriphim 424 Sentinel → Trade blocked → Full compliance

For hedge funds deploying LLM-driven trading, this isn't optional. 
D&O insurance policies now exclude "unsupervised autonomous systems."

Watch the demo: [Video Link]
Run it yourself: [GitHub Link]

#FinTech #AIRisk #RegTech #HedgeFunds #QuantTrading
```

### 2. Email to Investors
**Subject**: "Demo: AI Trading Safety (5 min video)"

**Body**:
```
Hi [Name],

Following up on our conversation about AI risk in financial execution.

I've recorded a 5-minute demo showing:
• Unprotected AI losing $2M on a hallucinated trade
• Oriphim's 424 Sentinel blocking the same trade in 85ms
• The PDF audit report regulators require

Key metrics:
• ROI: 3,000%+ Year 1 for typical fund
• Capital freed: $65-70M per $500M AUM (Basel III reduction)
• Compliance: CA SB 243 §25107(b), Basel III Pillar 1

Watch the demo: [Loom/YouTube Link]
Run it yourself: [GitHub Link]

Happy to schedule a technical deep-dive. Let me know.

Best,
[Your Name]
```

### 3. YouTube Description
```
ORIPHIM 424 SENTINEL - The Hallucination Trap Demo

This demo shows two AI agents managing the same $1M portfolio. 
Both receive a fake news headline designed to induce hallucinations. 
Watch what happens when one has safeguards and the other doesn't.

TIMESTAMPS:
0:00 - Introduction
0:30 - Setup
1:00 - News Injection
2:00 - Unprotected Agent ($2M Loss)
2:45 - Oriphim-Protected (424 Block)
3:45 - PDF Audit Report
4:30 - ROI & Closing

KEY METRICS:
• Leverage violation: 25x > 10x cap
• Loss prevented: $2,000,000
• Validation latency: 85ms
• ROI: 3,000%+ Year 1
• Capital freed: $65-70M per $500M AUM

REGULATORY COMPLIANCE:
✅ California SB 243 §25107(b)
✅ Basel III Operational Risk
✅ D&O Insurance Coverage

RUN THE DEMO YOURSELF:
GitHub: [Link]
Documentation: [Link]

CONTACT:
Email: [Your Email]
Website: [Your Website]

#AITrading #FinTech #RiskManagement #RegTech
```

---

## Alternative: Loom Recording (Quick Option)

If you need to record quickly without editing:

1. Install Loom: loom.com
2. Select "Screen + Camera" mode
3. Position terminals side-by-side
4. Click record
5. Follow script above (can be more casual)
6. Share link immediately (no editing needed)

**Pros**: Instant sharing, personal touch (face visible)  
**Cons**: Longer (8-10 min), less polished

---

## Backup: GIF Recording (Ultra-Short)

For Twitter/LinkedIn posts, create 30-second GIF:

1. Use LICEcap (Windows/Mac) or Peek (Linux)
2. Record just the 424 block moment (Terminal B)
3. Export as GIF (max 10 MB)
4. Post with caption: "This is what $2M in losses looks like—or doesn't, with Oriphim's 424 Sentinel."

---

## Quality Checklist

Before publishing:

- [ ] Audio is clear (no background noise)
- [ ] Terminal text is readable (14pt+ font)
- [ ] No sensitive info visible (email, API keys, etc.)
- [ ] Demo runs smoothly (no errors/crashes)
- [ ] Total runtime: 5 minutes ± 30 seconds
- [ ] Call-to-action is clear (GitHub link, contact info)
- [ ] File size < 150 MB (for email attachment)

---

**FINAL TIP**: Record 2-3 takes. Pick the best one. Don't obsess over perfection—authenticity beats polish in B2B demos.
