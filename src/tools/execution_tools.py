import yfinance as yf
from crewai.tools import tool
from typing import Dict

@tool("Execute Pairs Trade")
def execute_pairs_trade(ticker_leg1: str, ticker_leg2: str, action: str, total_value: float, hedge_ratio: float, slippage_bps: int = 10) -> Dict:
    """
    Simulates the execution of a pairs trade with realistic slippage modeling.
    
    Args:
        ticker_leg1 (str): Ticker for Leg 1 (e.g., "NEE").
        ticker_leg2 (str): Ticker for Leg 2 (e.g., "CWEN").
        action (str): "LONG" (Buy Spread: Buy Leg1, Sell Leg2) or "SHORT" (Sell Spread: Sell Leg1, Buy Leg2).
        total_value (float): Total capital to allocate to this trade (e.g., 10000).
        hedge_ratio (float): The beta from cointegration (e.g., 0.948).
        slippage_bps (int): Basis points of slippage to apply (default 10 bps = 0.1%).
        
    Returns:
        Dict: Trade confirmation with execution prices and share counts.
    """
    try:
        # 1. Fetch Real-Time Prices
        tickers = f"{ticker_leg1} {ticker_leg2}"
        data = yf.download(tickers, period="1d", progress=False, auto_adjust=True)['Close']
        
        if data.empty:
            return {"error": "Failed to fetch market prices for execution."}
            
        p1 = float(data[ticker_leg1].iloc[-1])
        p2 = float(data[ticker_leg2].iloc[-1])
        
        # 2. Calculate Slippage Factor
        # 10 bps = 0.0010. 
        # Buy Price = Market Price * (1 + slippage)
        # Sell Price = Market Price * (1 - slippage)
        slip_pct = slippage_bps / 10000.0
        
        # 3. Determine Side (Long vs Short)
        # Strategy: "LONG SPREAD" means Buy Leg 1, Sell Leg 2 (weighted by beta)
        
        # We split capital: Leg 1 gets half, Leg 2 gets half (simplified approximation for equal weight)
        # In precise pairs trading, we balance not by $, but by volatility, but 50/50 $ split is standard for this level.
        allocation_leg1 = total_value / 2
        allocation_leg2 = total_value / 2
        
        if action.upper() == "LONG_SPREAD" or action.upper() == "OPEN_LONG":
            # BUY Leg 1
            exec_p1 = p1 * (1 + slip_pct) # Pay more
            shares1 = allocation_leg1 / exec_p1
            
            # SELL Leg 2
            exec_p2 = p2 * (1 - slip_pct) # Receive less
            shares2 = allocation_leg2 / exec_p2
            
            leg1_side = "BUY"
            leg2_side = "SELL"
            
        elif action.upper() == "SHORT_SPREAD" or action.upper() == "OPEN_SHORT":
            # SELL Leg 1
            exec_p1 = p1 * (1 - slip_pct) # Receive less
            shares1 = allocation_leg1 / exec_p1
            
            # BUY Leg 2
            exec_p2 = p2 * (1 + slip_pct) # Pay more
            shares2 = allocation_leg2 / exec_p2
            
            leg1_side = "SELL"
            leg2_side = "BUY"
            
        elif action.upper() == "CLOSE":
            # Validates simply getting current value to close
            return {"info": "Closing logic handled by reversing original trade."}
            
        else:
            return {"error": f"Unknown action: {action}. Use LONG_SPREAD or SHORT_SPREAD."}

        return {
            "status": "FILLED",
            "timestamp": "Live",
            "slippage_applied": f"{slippage_bps} bps",
            "leg1": {
                "ticker": ticker_leg1,
                "side": leg1_side,
                "shares": round(shares1, 4),
                "avg_price": round(exec_p1, 2),
                "market_price": round(p1, 2)
            },
            "leg2": {
                "ticker": ticker_leg2,
                "side": leg2_side,
                "shares": round(shares2, 4),
                "avg_price": round(exec_p2, 2),
                "market_price": round(p2, 2)
            },
            "total_value_executed": total_value
        }

    except Exception as e:
        return {"error": str(e)}