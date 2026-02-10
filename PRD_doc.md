PRD: Oriphim V-Layer (v1.0 "Sentinel")

1. Objective
To provide a high-speed, headless API that intercepts AI agent outputs and validates them against Hard Constraints (Physics, Math, or Financial Rules) to prevent "Phase Transition" hallucinations.

2. User Stories
As a CTO of a Fintech/BioPharma firm, I need a way to ensure my AI agent doesn't execute a command that violates physical laws or risk-management parameters.

As a Developer, I need a single endpoint to "sanity check" my agent's reasoning before it hits my production database.

3. Functional Requirements (The "Pickaxe")
A. The Entropy Analyzer (Hallucination Detection)
Input: Multi-sample outputs from an LLM (Temperature > 0.7).

Logic: Calculate Semantic Entropy. If the agent provides three different "reasoning paths" for the same physics problem, the system must flag it as "Unstable."

Output: An "Entropy Score" (0.0 to 1.0).

B. The Hard Constraint Library (The Physics Engine)
Module 1 (Physics): Integration with basic PDE solvers (Partial Differential Equations) to verify if a suggested structural/chemical design is stable.

Module 2 (Financial): A hard-coded "VaR" (Value at Risk) checker. If an agent suggests a trade, the V-Layer checks the current order book and rejects it if it exceeds a $10k loss threshold, regardless of what the "AI" thinks.

C. The "Kill-Switch" Protocol
If Entropy Score > 0.4 OR any Hard Constraint is violated, the API returns Status: 403 (Logic Violation) and blocks execution.

4. Technical Stack (Optimized for your $300 Budget)
Language: Python (FastAPI).

Infrastructure: Vercel (Free tier) or a single $5/mo DigitalOcean Droplet.

Verification Tools: NumPy for math, Pydantic for strict data typing, and SciPy for physical constraints.

Database: None. This is a stateless pass-through (Infrastructure, not an app).

Actionable Directives for Development
Build the "Constraint Wrapper": Write a Python decorator that wraps any LLM call. It must take the output and run it through a check_logic() function before returning the value.

Define the "Physics Unit": Since you like physics, code a validator that checks for Conservation of Energy. If the AI suggests a system that outputs more energy than it takes in, the validator must kill the process. This is your "Proof of Concept."

Latency is the Killer: Your check must run in <200ms. High-frequency systems won't wait for a slow validator.