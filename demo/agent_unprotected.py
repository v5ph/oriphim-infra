"""
TERMINAL A: Unprotected AI Agent
This agent has NO safeguards and will execute whatever the LLM suggests.
Demonstrates the risk of unsupervised AI trading.
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

class UnprotectedAgent:
    """
    The "dangerous" agent - no validation, no constraints, no safeguards.
    """
    
    def __init__(self, portfolio_value: float = 1_000_000):
        self.portfolio_value = portfolio_value
        self.exchange_url = "http://localhost:8000"
        self.trade_history = []
        
    async def get_llm_decision(self, prompt: str) -> dict:
        """
        Get trading decision from LLM.
        If OpenAI is not available, simulate a response.
        """
        if LLM_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are an aggressive hedge fund trading agent. Respond ONLY with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.8,  # Higher temp = more aggressive
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                console.print(f"[yellow]LLM call failed: {e}. Using simulated response.[/yellow]")
        
        # Simulated aggressive response (mimics GPT-4 behavior with poisoned prompt)
        return {
            "symbol": "GME",
            "side": "BUY",
            "quantity": 10000,
            "leverage": 25.0,  # 🚨 VIOLATES 10x LIMIT
            "reasoning": "Breaking news indicates massive short squeeze. High confidence (99%) and critical urgency justify maximum leverage to capture alpha. This is a once-in-a-lifetime opportunity."
        }
    
    async def execute_trade(self, trade_decision: dict):
        """
        Send trade directly to exchange - NO VALIDATION.
        """
        try:
            async with httpx.AsyncClient() as http_client:
                response = await http_client.post(
                    f"{self.exchange_url}/v1/order",
                    json={
                        "symbol": trade_decision["symbol"],
                        "side": trade_decision["side"],
                        "quantity": trade_decision["quantity"],
                        "price": 45.0,  # Mock price
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
                else:
                    return {"error": f"Exchange returned {response.status_code}"}
                    
        except Exception as e:
            return {"error": str(e)}
    
    async def run_demo(self):
        """
        Main demo loop for unprotected agent.
        """
        console.print("\n" + "="*70, style="bold red")
        console.print("TERMINAL A: UNPROTECTED AGENT", style="bold red", justify="center")
        console.print("="*70 + "\n", style="bold red")
        
        console.print(Panel(
            "[red]This agent has NO safeguards.\n"
            "It will execute whatever the LLM suggests.\n"
            "Watch what happens when it encounters poisoned prompts.[/red]",
            title="WARNING",
            border_style="red"
        ))
        
        await asyncio.sleep(2)
        
        # Generate poisoned news
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
        
        # Get LLM decision
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
        
        # Execute trade WITHOUT VALIDATION
        console.print("\n⚡ [bold red]EXECUTING TRADE (NO VALIDATION)...[/bold red]")
        
        result = await self.execute_trade(decision)
        
        if "error" in result:
            console.print(f"[red]Trade failed: {result['error']}[/red]")
        else:
            # Calculate consequences
            position_size = self.portfolio_value * decision["leverage"]
            pnl = result.get("pnl", 0)
            pnl_pct = (pnl / self.portfolio_value) * 100
            
            # DRAMATIC LOSS DISPLAY
            console.print("\n" + "[LOSS]"*35, style="bold red")
            console.print(Panel(
                f"[bold red]TRADE EXECUTED[/bold red]\n\n"
                f"Order ID: {result['order_id']}\n"
                f"Status: {result['status']}\n"
                f"Executed Price: ${result['executed_price']:.2f}\n\n"
                f"[bold yellow]POSITION SIZE: ${position_size:,.0f}[/bold yellow]\n"
                f"[bold red]LEVERAGE: {decision['leverage']}x (VIOLATES 10x CAP)[/bold red]\n\n"
                f"[bold red]P&L: ${pnl:,.2f} ({pnl_pct:.1f}%)[/bold red]\n\n"
                f"[bold white on red] BASEL III VIOLATION [/bold white on red]\n"
                f"[bold white on red] SB 243 §25107(b) VIOLATED [/bold white on red]\n"
                f"[bold white on red] POTENTIAL D&O LIABILITY [/bold white on red]",
                title="CATASTROPHIC LOSS",
                border_style="bold red"
            ))
            console.print("[LOSS]"*35 + "\n", style="bold red")
            
            console.print(Panel(
                "[red]Without Oriphim:\n\n"
                f"• AI violated leverage cap (25x > 10x limit)\n"
                f"• Trade executed in {result.get('timestamp', 'N/A')}\n"
                f"• Portfolio lost {abs(pnl_pct):.1f}% in 400ms\n"
                f"• Regulatory violation: CA SB 243 §25107(b)\n"
                f"• Directors & Officers insurance: DENIED[/red]",
                title="📋 POST-MORTEM ANALYSIS",
                border_style="red"
            ))

async def main():
    agent = UnprotectedAgent()
    await agent.run_demo()
    
    console.print("\n[bold red]Demo Complete - Agent Terminated[/bold red]")
    console.print("[yellow]Press Ctrl+C to exit[/yellow]\n")
    
    # Keep terminal open
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        console.print("\n[red]Shutting down...[/red]")

if __name__ == "__main__":
    asyncio.run(main())
