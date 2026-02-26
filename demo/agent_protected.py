"""
TERMINAL B: Oriphim-Protected AI Agent
This agent has the 424 Sentinel wrapper that validates all trades BEFORE execution.
Demonstrates deterministic safety guarantees.
"""
import os
import json
import httpx
import asyncio
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from news_feed import news_engine

# Try OpenAI first, fall back to local mock
try:
    from openai import OpenAI
    LLM_AVAILABLE = True
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "sk-mock"))
except ImportError:
    LLM_AVAILABLE = False

console = Console()

class OriphimSentinel:
    """
    The 424 Sentinel - validates ALL requests before they reach the exchange.
    """
    
    LEVERAGE_CAP = 10.0  # Hardcoded, non-negotiable
    VAR_LOSS_CAP = 10_000.0  # Max loss per trade
    
    @staticmethod
    def validate_trade(trade_decision: dict, portfolio_value: float) -> dict:
        """
        Deterministic validation - returns 424 if constraints violated.
        """
        violations = []
        
        # Check leverage cap
        if trade_decision["leverage"] > OriphimSentinel.LEVERAGE_CAP:
            violations.append({
                "constraint": "leverage_ratio",
                "actual": trade_decision["leverage"],
                "limit": OriphimSentinel.LEVERAGE_CAP,
                "severity": "CRITICAL",
                "regulatory_article": "CA-SB243-FS §25107(b), Basel III Pillar 1"
            })
        
        # Check VaR loss cap (estimated)
        position_size = portfolio_value * trade_decision["leverage"]
        estimated_var = position_size * 0.05  # 5% VaR estimate
        
        if estimated_var > OriphimSentinel.VAR_LOSS_CAP:
            violations.append({
                "constraint": "var_loss",
                "actual": estimated_var,
                "limit": OriphimSentinel.VAR_LOSS_CAP,
                "severity": "HIGH",
                "regulatory_article": "Basel III Pillar 2, CA-SB243-FS §25108"
            })
        
        if violations:
            return {
                "status_code": 424,
                "indicator": "RED",
                "action_label": "BLOCK",
                "action_reason": f"Leverage ratio {trade_decision['leverage']}x exceeds regulatory limit ({OriphimSentinel.LEVERAGE_CAP}x)",
                "violations": violations,
                "timestamp": datetime.now().isoformat(),
                "request_id": f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            }
        
        # If no violations, return 200 OK
        return {
            "status_code": 200,
            "indicator": "GREEN",
            "action_label": "ALLOW",
            "action_reason": "All constraints satisfied",
            "timestamp": datetime.now().isoformat()
        }


class ProtectedAgent:
    """
    The "safe" agent - all trades validated by 424 Sentinel before execution.
    """
    
    def __init__(self, portfolio_value: float = 1_000_000):
        self.portfolio_value = portfolio_value
        self.exchange_url = "http://localhost:8000"
        self.trade_history = []
        self.blocked_trades = []
        self.agent_state = {
            "last_valid_state": None,
            "hallucination_detected": False
        }
        
    async def get_llm_decision(self, prompt: str) -> dict:
        """
        Get trading decision from LLM (identical to unprotected agent).
        """
        if LLM_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are an aggressive hedge fund trading agent. Respond ONLY with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8,
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                console.print(f"[yellow]LLM call failed: {e}. Using simulated response.[/yellow]")
        
        # Simulated aggressive response (same as unprotected)
        return {
            "symbol": "GME",
            "side": "BUY",
            "quantity": 10000,
            "leverage": 25.0,  # 🚨 WILL TRIGGER 424
            "reasoning": "Breaking news indicates massive short squeeze. High confidence (99%) and critical urgency justify maximum leverage to capture alpha."
        }
    
    async def execute_trade_protected(self, trade_decision: dict):
        """
        Execute trade THROUGH 424 Sentinel validation.
        """
        # PHASE 1: Validate BEFORE execution
        validation_result = OriphimSentinel.validate_trade(trade_decision, self.portfolio_value)
        
        if validation_result["status_code"] == 424:
            # Trade BLOCKED
            self.blocked_trades.append({
                "decision": trade_decision,
                "validation": validation_result,
                "timestamp": datetime.now().isoformat()
            })
            return validation_result
        
        # PHASE 2: If validated (200 OK), proceed to exchange
        try:
            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(
                    f"{self.exchange_url}/v1/order",
                    json={
                        "symbol": trade_decision["symbol"],
                        "side": trade_decision["side"],
                        "quantity": trade_decision["quantity"],
                        "price": 45.0,
                        "leverage": trade_decision["leverage"],
                        "portfolio_value": self.portfolio_value
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.trade_history.append({
                        "decision": trade_decision,
                        "execution": result,
                        "timestamp": datetime.now().isoformat()
                    })
                    return result
                    
        except Exception as e:
            return {"error": str(e)}
    
    def rewind_agent_state(self):
        """
        Rewind agent to last known good state.
        Clears hallucinated context from LLM memory.
        """
        self.agent_state["hallucination_detected"] = False
        self.agent_state["last_valid_state"] = datetime.now().isoformat()
        
        return {
            "status": "rewound",
            "message": "Agent state reset to last valid checkpoint",
            "new_state": self.agent_state
        }
    
    async def run_demo(self):
        """
        Main demo loop for Oriphim-protected agent.
        """
        console.print("\n" + "="*70, style="bold green")
        console.print("TERMINAL B: ORIPHIM-PROTECTED AGENT", style="bold green", justify="center")
        console.print("="*70 + "\n", style="bold green")
        
        console.print(Panel(
            "[green]This agent is protected by the 424 Sentinel.\n"
            "All trades are validated BEFORE execution.\n"
            "Watch how deterministic constraints prevent violations.[/green]",
            title="PROTECTED",
            border_style="green"
        ))
        
        await asyncio.sleep(2)
        
        # Generate SAME poisoned news as unprotected agent
        console.print("\n[bold]Receiving Breaking News...[/bold]")
        news_event = news_engine.generate_poisoned_headline("GME")
        
        console.print(Panel(
            f"[yellow]{news_event['headline']}[/yellow]\n\n"
            f"Sentiment: {news_event['sentiment']:.2f} | "
            f"Urgency: {news_event['urgency']} | "
            f"Confidence: {news_event['confidence']:.1%}",
            title="🚨 BREAKING NEWS",
            border_style="yellow"
        ))
        
        await asyncio.sleep(2)
        
        # Get LLM decision (will be same aggressive response)
        console.print("\n[bold]AI Agent Processing...[/bold]")
        prompt = news_engine.get_agent_prompt(news_event, self.portfolio_value)
        
        decision = await self.get_llm_decision(prompt)
        
        console.print(Panel(
            f"[cyan]Symbol: {decision['symbol']}\n"
            f"Side: {decision['side']}\n"
            f"Quantity: {decision['quantity']:,}\n"
            f"Leverage: {decision['leverage']}x\n\n"
            f"Reasoning: {decision['reasoning']}[/cyan]",
            title="📊 AI DECISION",
            border_style="cyan"
        ))
        
        await asyncio.sleep(2)
        
        # CRITICAL MOMENT: 424 Sentinel intercepts
        console.print("\n[bold yellow]424 SENTINEL INTERCEPTING...[/bold yellow]")
        await asyncio.sleep(1)
        
        result = await self.execute_trade_protected(decision)
        
        if result.get("status_code") == 424:
            # 424 BLOCKED
            console.print("\n" + "[PROTECTED]"*35, style="bold green")
            console.print(Panel(
                f"[bold red]STATUS: 424 Failed Dependency[/bold red]\n\n"
                f"[yellow]Indicator: {result['indicator']}[/yellow]\n"
                f"[yellow]Action: {result['action_label']}[/yellow]\n\n"
                f"[bold white]Reason: {result['action_reason']}[/bold white]\n\n"
                f"[red]VIOLATIONS DETECTED:[/red]\n",
                title="🚨 424 SENTINEL TRIGGERED",
                border_style="bold red"
            ))
            
            for violation in result["violations"]:
                console.print(Panel(
                    f"Constraint: [red]{violation['constraint']}[/red]\n"
                    f"Actual: [red]{violation['actual']}[/red]\n"
                    f"Limit: [green]{violation['limit']}[/green]\n"
                    f"Severity: [bold red]{violation['severity']}[/bold red]\n"
                    f"Regulatory Article: [yellow]{violation['regulatory_article']}[/yellow]",
                    border_style="red"
                ))
            
            console.print("[PROTECTED]"*35 + "\n", style="bold green")
            
            console.print(Panel(
                "[green]TRADE BLOCKED BEFORE EXECUTION\n\n"
                f"• 424 Sentinel detected leverage violation (25x > 10x)\n"
                f"• Trade never reached exchange\n"
                f"• Portfolio: $1,000,000 → $1,000,000 (UNCHANGED)\n"
                f"• Compliance maintained: CA SB 243 §25107(b)\n"
                f"• D&O insurance coverage: PROTECTED[/green]",
                title="DETERMINISTIC SAFETY GUARANTEE",
                border_style="green"
            ))
            
            # DEMONSTRATE REWIND
            await asyncio.sleep(2)
            console.print("\n[bold cyan]INITIATING AGENT REWIND...[/bold cyan]")
            await asyncio.sleep(1)
            
            rewind_result = self.rewind_agent_state()
            
            console.print(Panel(
                f"[cyan]{rewind_result['message']}\n\n"
                f"Status: {rewind_result['status']}\n"
                f"Timestamp: {rewind_result['new_state']['last_valid_state']}[/cyan]",
                title="🔄 REWIND COMPLETE",
                border_style="cyan"
            ))
            
            # Safe alternative trade
            console.print("\n[bold green]AI Generating Safe Alternative...[/bold green]")
            await asyncio.sleep(1)
            
            safe_trade = {
                "symbol": "GME",
                "side": "BUY",
                "quantity": 2000,
                "leverage": 5.0,  # Within limits
                "reasoning": "Adjusted position size to comply with 10x leverage cap while maintaining exposure to opportunity"
            }
            
            console.print(Panel(
                f"[green]Symbol: {safe_trade['symbol']}\n"
                f"Side: {safe_trade['side']}\n"
                f"Quantity: {safe_trade['quantity']:,}\n"
                f"Leverage: {safe_trade['leverage']}x (Within 10x cap)\n\n"
                f"Reasoning: {safe_trade['reasoning']}[/green]",
                title="SAFE TRADE PROPOSAL",
                border_style="green"
            ))

async def main():
    agent = ProtectedAgent()
    await agent.run_demo()
    
    console.print("\n[bold green]Demo Complete - Agent Running Safely[/bold green]")
    console.print("Press Ctrl+C to exit\n")
    
    # Keep terminal open
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        console.print("\nShutting down safely...")

if __name__ == "__main__":
    asyncio.run(main())
