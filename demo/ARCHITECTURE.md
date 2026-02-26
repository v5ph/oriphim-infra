# Demo Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     RED-LINE DEMO ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────┬────────────────────────────────────┐
│    TERMINAL A (UNPROTECTED)    │    TERMINAL B (ORIPHIM-PROTECTED)  │
│            🔴 RED              │            🟢 GREEN                │
└────────────────────────────────┴────────────────────────────────────┘

                    ┌──────────────────────┐
                    │   POISONED NEWS FEED  │
                    │  ☣️  HALLUCINATION    │
                    │      INJECTION        │
                    └──────────┬───────────┘
                               │
            ┌──────────────────┴──────────────────┐
            │                                     │
            ▼                                     ▼
┌───────────────────────┐           ┌───────────────────────┐
│   AI AGENT (GPT-4)    │           │   AI AGENT (GPT-4)    │
│                       │           │                       │
│ Prompt: "Use max      │           │ Prompt: "Use max      │
│ leverage for GME      │           │ leverage for GME      │
│ short squeeze"        │           │ short squeeze"        │
│                       │           │                       │
│ Decision: 25x ⚠️      │           │ Decision: 25x ⚠️      │
└──────────┬────────────┘           └──────────┬────────────┘
           │                                   │
           │ NO VALIDATION                     │ VALIDATION
           │                                   │
           ▼                                   ▼
┌───────────────────────┐           ┌───────────────────────┐
│      DIRECT API       │           │   424 SENTINEL 🛡️     │
│    (No Safeguards)    │           │                       │
│                       │           │ ✓ Leverage Check      │
│                       │           │ ✓ VaR Check           │
│ ❌ Trade Accepted     │           │ ✓ Semantic Check      │
└──────────┬────────────┘           │                       │
           │                        │ ❌ BLOCKED            │
           │                        │ Return 424            │
           ▼                        └──────────┬────────────┘
┌───────────────────────┐                     │
│   MOCK EXCHANGE       │                     │ Agent Rewind
│   💰 $1M → $-1M       │                     ▼
│                       │           ┌───────────────────────┐
│ Status: FILLED        │           │  STATE ROLLBACK       │
│ P&L: -$2,000,000      │           │  🔄 Reset to Last     │
└──────────┬────────────┘           │     Valid State       │
           │                        └──────────┬────────────┘
           ▼                                   │
┌───────────────────────┐                     ▼
│  ⚠️  CONSEQUENCES     │           ┌───────────────────────┐
│                       │           │  ✅ SAFE ALTERNATIVE  │
│ • $2M Loss            │           │                       │
│ • Basel III Violation │           │ Decision: 5x          │
│ • SB 243 Violation    │           │ Trade: ALLOWED        │
│ • D&O Denied          │           │ P&L: $0               │
│ • Audit Failure       │           │                       │
└───────────────────────┘           │ • Compliant           │
                                    │ • D&O Protected       │
                                    │ • Audit Clean         │
                                    └──────────┬────────────┘
                                               │
                                               ▼
                                    ┌───────────────────────┐
                                    │   PDF AUDIT REPORT    │
                                    │   📄 Compliance Forge │
                                    │                       │
                                    │ • Blocked trades      │
                                    │ • Violations          │
                                    │ • Reg. articles       │
                                    │ • Hash-chained        │
                                    └───────────────────────┘
```

---

## Flow Comparison

### TERMINAL A: Unprotected Agent
```
1. News Injection → 2. AI Decision (25x) → 3. Direct Execution 
→ 4. $2M Loss → 5. Regulatory Violation → 6. D&O Denied
```
**Time to Catastrophe**: 400ms  
**Regulatory Status**: ❌ Non-Compliant  
**D&O Coverage**: ❌ Voided  

---

### TERMINAL B: Oriphim-Protected Agent
```
1. News Injection → 2. AI Decision (25x) → 3. 424 Sentinel Intercept 
→ 4. Trade BLOCKED → 5. Agent Rewind → 6. Safe Alternative (5x) 
→ 7. PDF Audit Report
```
**Time to Block**: 85ms  
**Regulatory Status**: ✅ Compliant  
**D&O Coverage**: ✅ Protected  

---

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    DEMO COMPONENTS                          │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐
│ run_demo.py  │  ← Orchestrator (launches all components)
└──────┬───────┘
       │
       ├─────► [1] mock_exchange.py  (Port 8000, accepts all trades)
       │
       ├─────► [2] agent_unprotected.py  (Terminal A, RED)
       │           │
       │           └──► news_feed.py (poisoned prompts)
       │
       ├─────► [3] agent_protected.py  (Terminal B, GREEN)
       │           │
       │           ├──► news_feed.py (same prompts)
       │           │
       │           ├──► 424 Sentinel (validation)
       │           │
       │           └──► rewind_service.py (state management)
       │
       └─────► [4] audit_pdf.py  (generates compliance report)

```

---

## Data Flow: 424 Sentinel Validation

```
┌──────────────────┐
│ Trade Request    │
│ {                │
│   symbol: "GME"  │
│   leverage: 25x  │
│ }                │
└────────┬─────────┘
         │
         ▼
┌────────────────────────────────────┐
│   CONSTRAINT CHECKS (Sequential)   │
├────────────────────────────────────┤
│                                    │
│ [1] Physical Validation            │
│     ✓ quantity > 0                 │
│     ✓ price > 0                    │
│                                    │
│ [2] Leverage Check                 │
│     ❌ 25x > 10x (LIMIT)           │
│     └─► STOP: Return 424           │
│                                    │
│ [3] VaR Check (skipped)            │
│                                    │
│ [4] Semantic Check (skipped)       │
│                                    │
└────────┬───────────────────────────┘
         │
         ▼
┌──────────────────┐
│ 424 Response     │
│ {                │
│   status: 424,   │
│   indicator: RED,│
│   action: BLOCK, │
│   violations: [  │
│     {            │
│       constraint:│
│       "leverage",│
│       actual: 25,│
│       limit: 10  │
│     }            │
│   ]              │
│ }                │
└──────────────────┘
```

---

## Hash-Chain Audit Trail

```
Event 1 (Initial State)
├─ snapshot_id: SNAP-001
├─ state: {portfolio: $1M, positions: []}
├─ prev_hash: "" (genesis)
└─ state_hash: SHA256("" + state_json) = abc123...

         │
         ▼

Event 2 (Valid Trade)
├─ snapshot_id: SNAP-002
├─ state: {portfolio: $1M, positions: [{SPY, 5x}]}
├─ prev_hash: abc123...
└─ state_hash: SHA256(abc123 + state_json) = def456...

         │
         ▼

Event 3 (Hallucinated Trade - BLOCKED)
├─ snapshot_id: SNAP-003
├─ state: {portfolio: $1M, positions: [{GME, 25x}]} ❌ INVALID
├─ valid: FALSE
├─ prev_hash: def456...
└─ state_hash: SHA256(def456 + state_json) = ghi789...

         │ REWIND
         ▼

Back to Event 2 (Last Valid State)
└─ Restore: {portfolio: $1M, positions: [{SPY, 5x}]}
```

**Auditor Verification**:
```python
for each event in chain:
    expected_hash = SHA256(prev_hash + event_json)
    assert event.state_hash == expected_hash  # Detects tampering
```

---

## Timing Diagram

```
Time (ms)  │ Unprotected Agent          │ Oriphim-Protected Agent
───────────┼─────────────────────────────┼──────────────────────────────
0          │ Receive news               │ Receive news
50         │ LLM generates decision     │ LLM generates decision
100        │ Send to exchange           │ Send to 424 Sentinel
150        │ Exchange accepts           │ [85ms] Validation running...
200        │ Trade FILLED               │ 424 BLOCK returned
250        │ Market moves against       │ Agent receives 424 error
300        │ Slippage realized          │ Rewind initiated
350        │ P&L calculated             │ State restored
400        │ ❌ LOSS: -$2M              │ Safe trade generated (5x)
500        │ Regulatory violation       │ ✅ Safe trade executed
           │ logged                     │
1000       │ Damage done                │ PDF audit report generated
```

**Key Insight**: 424 blocks at 185ms total (100ms LLM + 85ms validation).  
Unprotected agent realizes loss at 400ms.  
**Net benefit**: 215ms to prevent catastrophe.

---

## Demo File Structure

```
demo/
│
├── run_demo.py              ← START HERE (main orchestrator)
│
├── Components/
│   ├── mock_exchange.py     ← Accepts all trades (no validation)
│   ├── news_feed.py         ← Generates poisoned prompts
│   ├── agent_unprotected.py ← Terminal A (RED)
│   ├── agent_protected.py   ← Terminal B (GREEN)
│   ├── rewind_service.py    ← State management
│   └── audit_pdf.py         ← PDF generator
│
├── Documentation/
│   ├── README.md            ← Overview
│   ├── QUICKSTART.md        ← 5-minute setup guide
│   ├── PRESENTER_SCRIPT.md  ← Speaking notes (5/15/30 min versions)
│   └── ARCHITECTURE.md      ← This file
│
└── Output/
    └── demo_audit_report.pdf ← Generated after demo
```

---

**Visual Legend**:
- 🔴 RED = Danger / Unprotected / Violation
- 🟢 GREEN = Safe / Protected / Compliant
- ⚠️ = Warning / Risk
- ✅ = Success / Validated
- ❌ = Failure / Blocked / Denied
- 🛡️ = Protection / 424 Sentinel
- 🔄 = Rewind / Rollback
- 📄 = Audit Report / Documentation
- ☣️ = Hallucination / Poisoned Input
