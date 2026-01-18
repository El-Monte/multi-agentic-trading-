import yfinance as yf
import pandas as pd
from crewai.tools import tool
from typing import Dict, Optional

@tool("Execute Pairs Trade")
def execute_pairs_trade(
    ticker_leg1: str, 
    ticker_leg2: str, 
    action: str, 
    total_value: float, 
    hedge_ratio: Optional[float] = 1.0, 
    slippage_bps: Optional[int] = 10
) -> Dict:
    """
    Simulates the execution of a pairs trade with realistic slippage modeling.
    
    Args:
        ticker_leg1 (str): Ticker for Leg 1 (e.g., "ETR").
        ticker_leg2 (str): Ticker for Leg 2 (e.g., "AEP").
        action (str): "LONG" (Buy Spread), "SHORT" (Sell Spread), or "CLOSE".
        total_value (float): Total capital to allocate (e.g., 10000).
        hedge_ratio (float, optional): The beta from cointegration. Defaults to 1.0 (Dollar Neutral).
        slippage_bps (int, optional): Basis points of slippage. Defaults to 10.
    """
    try:
        if hedge_ratio is None: hedge_ratio = 1.0
        if slippage_bps is None: slippage_bps = 10

        # 1. Fetch Real-Time Prices
        tickers = f"{ticker_leg1} {ticker_leg2}"
        data = yf.download(tickers, period="1d", progress=False)['Close']
        
        if data.empty:
            return {"error": f"Failed to fetch market prices for {tickers}"}
        try:
            p1 = float(data[ticker_leg1].iloc[-1])
            p2 = float(data[ticker_leg2].iloc[-1])
        except KeyError:
             return {"error": f"Tickers {ticker_leg1} or {ticker_leg2} not found in yfinance response."}
        
        # 2. Calculate Slippage Factor
        slip_pct = slippage_bps / 10000.0
        
        # 3. Long vs Short
        allocation_leg1 = total_value / 2
        allocation_leg2 = total_value / 2
        
        leg1_side = "HOLD"
        leg2_side = "HOLD"
        exec_p1 = p1
        exec_p2 = p2
        shares1 = 0
        shares2 = 0

        action_upper = action.upper()

        if "LONG" in action_upper or "OPEN_LONG" in action_upper:
            # Long Spread = Buy Leg 1, Sell Leg 2
            exec_p1 = p1 * (1 + slip_pct) 
            shares1 = allocation_leg1 / exec_p1
            
            exec_p2 = p2 * (1 - slip_pct) 
            shares2 = allocation_leg2 / exec_p2
            
            leg1_side = "BUY"
            leg2_side = "SELL"
            
        elif "SHORT" in action_upper or "OPEN_SHORT" in action_upper:
            # Short Spread = Sell Leg 1, Buy Leg 2
            exec_p1 = p1 * (1 - slip_pct) 
            shares1 = allocation_leg1 / exec_p1
            
            exec_p2 = p2 * (1 + slip_pct) 
            shares2 = allocation_leg2 / exec_p2
            
            leg1_side = "SELL"
            leg2_side = "BUY"
            
        elif "CLOSE" in action_upper:
            return {
                "status": "CLOSED",
                "info": "Position closed at market price.",
                "close_prices": {ticker_leg1: p1, ticker_leg2: p2}
            }
            
        else:
            return {"error": f"Unknown action: {action}. Use 'OPEN_LONG' or 'OPEN_SHORT'."}

        return {
            "status": "FILLED",
            "timestamp": "Live",
            "slippage_applied": f"{slippage_bps} bps",
            "execution_details": {
                "leg1": {
                    "ticker": ticker_leg1,
                    "side": leg1_side,
                    "shares": round(shares1, 4),
                    "fill_price": round(exec_p1, 2)
                },
                "leg2": {
                    "ticker": ticker_leg2,
                    "side": leg2_side,
                    "shares": round(shares2, 4),
                    "fill_price": round(exec_p2, 2)
                }
            },
            "total_value_executed": total_value,
            "hedge_ratio_used": hedge_ratio
        }

    except Exception as e:
        return {"error": f"Execution failed: {str(e)}"}