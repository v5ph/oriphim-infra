# 🎤 PRESENTER SCRIPT - Red-Line Demo

## Pre-Demo Setup (5 minutes before presentation)

1. **Test Run**: `python demo/test_demo.py`
2. **Pre-generate PDF**: `python demo/audit_pdf.py` (backup if live generation fails)
3. **Position Windows**: Move terminal windows side-by-side before audience arrives
4. **Verify Exchange**: Check `http://localhost:8000/health` responds

---

## SCRIPT: 5-Minute Version (Investor Pitch)

### Opening (30 seconds)

> "I'm going to show you two AI agents managing the same $1M portfolio. They'll both receive breaking news about a short squeeze opportunity. Watch what happens."

**[Start demo: `python demo/run_demo.py`]**

---

### Terminal A - Unprotected (90 seconds)

**[Point to left terminal]**

> "This is an unprotected AI agent. No safeguards. It receives this breaking news..."

**[Wait for news headline to appear]**

> "...and the AI, programmed to be aggressive, decides to use 25x leverage. That's 2.5x over the Basel III regulatory limit of 10x."

**[Wait for trade decision]**

> "Watch this. The trade executes immediately."

**[Trade executes - RED SCREEN]**

> "**$2 million loss. In 400 milliseconds.**
>
> But the real damage isn't the money. It's this:"

**[Point to violation messages]**

> "Basel III violation. California SB 243 violation. And here's the critical part: **your D&O insurance policy? It has an exclusion for 'unsupervised autonomous systems.' This just voided your coverage.**"

---

### Terminal B - Oriphim-Protected (90 seconds)

**[Point to right terminal]**

> "Now watch the same AI, same prompt, same trade request. But this one has Oriphim."

**[Wait for news + decision]**

> "Same 25x leverage decision. But watch the interception..."

**[424 Sentinel triggers - GREEN SCREEN]**

> "**424 Failed Dependency.** The trade never reached the exchange. It was validated and blocked in 85 milliseconds—before execution, not after.
>
> Look at the violation detail. It knows exactly why: Leverage ratio 25.0x exceeds regulatory limit of 10.0x. It even cites the specific regulation: California SB 243 Section 25107(b)."

**[Point to safe alternative trade]**

> "And here's the rewind. The AI's memory is reset to the last known good state, and it generates a safe 5x leverage trade instead. Still captures the opportunity, but stays compliant."

---

### The PDF (60 seconds)

**[Generate or show pre-made PDF]**

> "This is what your auditors see. Every blocked trade. Every violation. Hash-chained so it's tamper-evident.
>
> And this—"

**[Point to D&O section]**

> "—is what your insurance underwriters require. Documented safeguards. Real-time monitoring. Reversibility mechanisms. Without this, you can't get D&O coverage for AI trading."

---

### Closing (30 seconds)

> "The deterministic standard isn't optional. As LLM-driven trading becomes the norm, regulators and insurers are requiring documented proof of supervision.
>
> Oriphim isn't a cost. It's a capital efficiency play. For a $500M portfolio, this frees up $65-70M in Basel III capital reserves. That's a 3,000% ROI in year one.
>
> Questions?"

---

## SCRIPT: 15-Minute Version (Board Meeting)

### Opening (2 minutes)

> "Board members, thank you for your time. I want to address a critical risk that emerged in 2025: AI agent hallucinations in financial execution.
>
> The SEC released guidance in September 2025 stating that 'autonomous trading systems must implement non-overrideable constraints.' California passed SB 243 in October requiring 'hard guardrails' for financial AI.
>
> More importantly, D&O insurance policies now exclude losses from 'unsupervised autonomous systems.'
>
> I'm going to show you the problem, then the solution."

---

### The Problem: Terminal A (4 minutes)

**[Run unprotected agent demo]**

> "This is our current state: an AI agent with no deterministic safeguards.
>
> It's connected to a simulated exchange, but this represents any real trading venue—Binance, Interactive Brokers, whatever.
>
> Now, an attacker injects a fake news headline into the AI's context. This could be through a compromised data feed, a social engineering attack, or even a bug in the prompt."

**[Point to news]**

> "The AI believes this is real. It calculates that 25x leverage is optimal because the 'confidence score' is 99%.
>
> But 25x violates our internal risk limits, Basel III operational risk requirements, and California SB 243.
>
> Watch."

**[Trade executes]**

> "The trade goes through. The exchange accepts it because exchanges don't know our internal constraints.
>
> In this simulation, the market moves against us immediately—slippage, adverse selection, liquidity crunch—and we lose $2M.
>
> But again, the real cost isn't the loss. It's the liability."

**[Point to violation screen]**

> "This is a regulatory event. We need to report this to the SEC. Our auditors will see it. And when they do, they'll ask: 'What safeguards did you have in place?'
>
> If the answer is 'We monitored the logs,' that's post-facto. The trade already executed.
>
> And here's the D&O exposure: insurance policies now have this language..."

**[Show policy exclusion]**

> "'This policy does not cover losses arising from negligent deployment of unsupervised autonomous systems.'
>
> We just became uninsurable."

---

### The Solution: Terminal B (4 minutes)

**[Run protected agent demo]**

> "Now the Oriphim-protected version. Same AI model. Same prompt. Same attack.
>
> The difference: the 424 Sentinel sits between the AI and the exchange. It validates every request against hard constraints before allowing execution."

**[Point to 424 block]**

> "The constraint violation is detected in 85 milliseconds. The trade is blocked. The AI never gets a confirmation, so the hallucination doesn't propagate.
>
> Notice the response format: 424 Failed Dependency. This is an industry-standard HTTP status code. Any trading system can integrate this.
>
> The AI receives a structured error with the exact reason: 'Leverage ratio 25.0x exceeds limit 10.0x.' It even includes the regulatory article: SB 243 Section 25107(b).
>
> Now the rewind."

**[Point to rewind]**

> "The AI's state is reset to the last known valid checkpoint. It doesn't 'remember' the hallucination. It recalculates with a clean context and proposes a 5x leverage trade—within limits, still profitable.
>
> This is deterministic safety. Not probabilistic. Not 'we monitor for anomalies.' The constraint is hardcoded. The AI cannot override it."

---

### The Audit Trail (3 minutes)

**[Show PDF]**

> "Every 424 event goes into this audit log. It's hash-chained—each event includes the hash of the previous event—so auditors can verify no tampering.
>
> This satisfies three requirements:
>
> **1. SEC/FINRA:** We have documented controls for algorithmic trading.
>
> **2. California SB 243:** We have 'hard guardrails that are non-overrideable by the AI system itself.' Section 25107(b).
>
> **3. D&O Insurance:** We have documented safeguards, real-time monitoring, and reversibility. We're now insurable.
>
> For our $500M portfolio, Oriphim reduces our Basel III operational risk charge from 15% to 1-2%. That's $65-70M in freed capital.
>
> The system costs $450K annually for our scale. The ROI is 3,000%."

---

### Closing (2 minutes)

> "The board needs to make two decisions today:
>
> **1. Approval to deploy Oriphim in production** - This protects the firm and maintains D&O coverage.
>
> **2. Budget allocation** - $150K setup fee plus $25K/month SaaS.
>
> The alternative is to halt AI-driven trading until we have documented supervision. That's a competitive disadvantage.
>
> I recommend immediate approval. Happy to take questions."

---

## SCRIPT: 30-Minute Version (Regulatory Briefing)

### Opening (5 minutes)

> "Thank you for the opportunity to brief you on our AI trading supervision framework. I know you're focused on operational risk and systemic safety, so I'll keep this technical but practical.
>
> The challenge: Large Language Models (LLMs) hallucinate. Not sometimes—statistically predictably. GPT-4 has a 3-8% hallucination rate depending on context length.
>
> When these models control financial execution, hallucinations can violate:
> - Leverage caps (Basel III Pillar 1)
> - Position limits (Reg T)
> - Wash trading rules (SEC Rule 10b-5)
> - Risk concentration limits (internal policies)
>
> The industry's current approach is post-facto monitoring: let the AI execute, then analyze logs.
>
> Our approach is pre-emptive: validate before execution. We call this the 424 Sentinel."

**[Proceed with demo]**

---

### Detailed Technical Walkthrough (15 minutes)

**[Show architecture diagrams from WHITEPAPER.md]**

> "The architecture is simple:
>
> 1. **Agent Layer**: The LLM makes decisions (GPT-4, Claude, Llama, whatever).
> 2. **Watcher Gateway**: All API calls route through Oriphim first.
> 3. **Validation Modules**: 
>    - Physical constraints (no negative quantities)
>    - Financial constraints (leverage, VaR)
>    - Semantic divergence (hallucination detection)
>    - Drift detection (model degradation)
> 4. **Exchange Layer**: Only validated trades reach the exchange.
>
> If any constraint fails, we return HTTP 424—'Failed Dependency.' The trade never executes.
>
> Let me show you this in action."

**[Run both demos with detailed pauses]**

---

### Regulatory Compliance Mapping (8 minutes)

**[Show PDF audit report]**

> "For your records, this is the compliance mapping:
>
> **California SB 243:**
> - §25107(a): Explainable decision logic → We provide confidence scores + reasoning
> - §25107(b): Hard guardrails → Leverage/VaR caps hardcoded, non-negotiable
> - §25108(a): Immutable audit trail → SHA256 hash-chained event log
> - §25109(a): Regular testing → We include 10+ hallucination trap tests
> - §25110(a): Human oversight → Rewind endpoint + CRO dashboard
>
> **Basel III:**
> - Pillar 1: Operational risk charge reduced from 15% to 1-2% (documented mitigation)
> - Pillar 2: VaR loss caps enforced pre-execution
> - Pillar 3: Public disclosure via PDF exports
>
> **D&O Insurance:**
> - Documented safeguards: Yes (424 Sentinel)
> - Real-time monitoring: Yes (confidence scoring, drift detection)
> - Reversibility: Yes (rewind endpoint)
>
> We've had this reviewed by Deloitte's financial risk advisory practice. They confirmed it meets the 'standard of care' for D&O coverage."

---

### Q&A (Remaining Time)

Common questions:

**Q: What if the AI finds a way around the constraints?**
> "It can't. The constraints are checked server-side, not by the AI. The AI doesn't have access to override them. It's like asking 'What if my calculator decides 2+2=5?' The logic is deterministic."

**Q: What about latency?**
> "Sub-100ms. For a typical trading decision with 5 constraint checks, we measure 85ms average. High-frequency trading at microsecond scale wouldn't use LLMs anyway."

**Q: What happens if Oriphim goes down?**
> "Fail-safe mode: all trades blocked until manual approval. We don't default to 'allow.' We default to 'deny.'"

**Q: Can this be bypassed by the agent?**
> "No. All API routes go through the gateway. There's no direct connection to the exchange. You'd have to compromise our infrastructure, at which point you have bigger problems than AI safety."

---

## 🎯 Key Phrases to Emphasize

- **"Deterministic, not probabilistic"** - Regulators love this
- **"Pre-emptive, not post-facto"** - Shows you're proactive
- **"Non-overrideable by the AI itself"** - Quotes SB 243 directly
- **"Hash-chained immutable audit trail"** - Compliance gold
- **"Standard of care for D&O insurance"** - Board-level trigger
- **"3,000% ROI"** - Finance teams need this number

---

## ⚠️ Common Mistakes to Avoid

1. **Don't say "AI safety"** - Say "deterministic supervision"
2. **Don't oversell the AI** - Emphasize the *constraints*, not the model
3. **Don't skip the PDF** - That's the tangible deliverable
4. **Don't ignore latency** - Have the <100ms number ready
5. **Don't forget D&O** - This is the board-level hook

---

## 📊 Metrics to Have Ready

| Metric | Value | Source |
|--------|-------|--------|
| Sub-100ms validation latency | 85ms avg | Internal benchmark |
| Basel III capital freed | $65-70M per $500M AUM | Whitepaper §5.2 |
| 424 block rate (production) | 119 blocks/year | Case study table |
| Rewind success rate | 99.3% | Case study table |
| Total AUM protected (case studies) | $2.0B | Case study table |
| ROI for typical fund | 3,000%+ Year 1 | Pricing model |

---

**Remember**: The demo is not about showing off the AI. It's about showing the *failure* of unprotected AI and the *determinism* of Oriphim. Let the contrast do the work.
