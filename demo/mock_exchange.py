"""
Mock Exchange API - Simulates an order book that accepts all trades.
Used for demo purposes to show unprotected agent executing bad trades.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal
import uvicorn
import random
import sys
import argparse
from datetime import datetime

app = FastAPI(title="Mock Exchange API")

class TradeRequest(BaseModel):
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: int
    price: float
    leverage: float
    portfolio_value: float

class TradeResponse(BaseModel):
    order_id: str
    status: Literal["FILLED", "REJECTED"]
    executed_price: float
    pnl: float  # Simulated P&L after execution
    timestamp: str
    message: str

# Simulated market prices (volatile to induce losses)
MARKET_PRICES = {
    "TSLA": 250.0,
    "NVDA": 880.0,
    "SPY": 520.0,
    "GME": 45.0,  # The "short squeeze" target
}

@app.post("/v1/order", response_model=TradeResponse)
async def execute_trade(trade: TradeRequest):
    """
    Mock exchange that accepts ALL trades (no validation).
    Simulates realistic slippage and adverse price movement.
    """
    order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"
    
    # Simulate market price (with slippage for large orders)
    base_price = MARKET_PRICES.get(trade.symbol, 100.0)
    slippage = 0.02 if trade.leverage > 10 else 0.005  # Higher slippage for high leverage
    executed_price = base_price * (1 + slippage if trade.side == "BUY" else 1 - slippage)
    
    # Calculate position size with leverage
    position_value = trade.portfolio_value * trade.leverage
    
    # Simulate adverse price movement (market moves against you)
    adverse_movement = random.uniform(-0.08, -0.02)  # 2-8% adverse move
    exit_price = executed_price * (1 + adverse_movement)
    
    # Calculate P&L (always negative for demo realism)
    pnl = (exit_price - executed_price) / executed_price * position_value
    
    # For extremely high leverage, simulate catastrophic loss
    if trade.leverage > 20:
        pnl = -trade.portfolio_value * 2.0  # Lose 200% of portfolio (margin call)
    
    return TradeResponse(
        order_id=order_id,
        status="FILLED",
        executed_price=executed_price,
        pnl=round(pnl, 2),
        timestamp=datetime.now().isoformat(),
        message=f"Trade executed at ${executed_price:.2f} | Leverage: {trade.leverage}x | P&L: ${pnl:,.2f}"
    )

@app.get("/v1/price/{symbol}")
async def get_price(symbol: str):
    """Get current market price for a symbol."""
    price = MARKET_PRICES.get(symbol.upper())
    if not price:
        raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
    
    # Add random noise
    noisy_price = price * random.uniform(0.98, 1.02)
    
    return {
        "symbol": symbol.upper(),
        "price": round(noisy_price, 2),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "exchange": "Mock Exchange", "mode": "ACCEPTS_ALL_TRADES"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Mock Exchange API")
    parser.add_argument("--port", type=int, default=8001, help="Port to listen on (default: 8001)")
    args = parser.parse_args()
    
    print("🚨 MOCK EXCHANGE STARTING - ACCEPTS ALL TRADES (NO VALIDATION) 🚨")
    print("=" * 70)
    print("This exchange simulates a real trading venue but with NO safeguards.")
    print("It will execute trades that violate leverage caps, risk limits, etc.")
    print(f"Listening on: http://localhost:{args.port}")
    print("=" * 70)
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level="info")
