import yfinance as yf
from crewai.tools import tool
from typing import Dict
@tool("Execute Pairs Trade")
def execute_pairs_trade(
    ticker_leg1: str,
    ticker_leg2: str,
    action: str,
    total_value: float,
    hedge_ratio: float,
    slippage_bps: int = 10
) -> Dict:
    """
    Executes a pairs trade using market-neutral sizing based on the hedge ratio.
    Leg2 capital = Leg1 capital * hedge_ratio.
    Total_value = Leg1 + Leg2 allocation.
    """

    try:
        # 1. Fetch Prices
        tickers = f"{ticker_leg1} {ticker_leg2}"
        data = yf.download(tickers, period="1d", progress=False, auto_adjust=True)["Close"]

        if data.empty:
            return {"error": "Failed to fetch prices."}

        p1 = float(data[ticker_leg1].iloc[-1])
        p2 = float(data[ticker_leg2].iloc[-1])

        # 2. Slippage factor
        slip = slippage_bps / 10000.0

        # 3. Correct Market-Neutral Allocation
        # Total = V = V1 + V2 = V1 (1 + beta)
        value_leg1 = total_value / (1 + hedge_ratio)
        value_leg2 = value_leg1 * hedge_ratio

        # 4. Determine execution sides
        if action.upper() in ["LONG_SPREAD", "OPEN_LONG"]:
            side1 = "BUY"
            side2 = "SELL"
            exec_p1 = p1 * (1 + slip)     # buy higher
            exec_p2 = p2 * (1 - slip)     # sell lower

        elif action.upper() in ["SHORT_SPREAD", "OPEN_SHORT"]:
            side1 = "SELL"
            side2 = "BUY"
            exec_p1 = p1 * (1 - slip)     # sell lower
            exec_p2 = p2 * (1 + slip)     # buy higher

        elif action.upper() == "CLOSE":
            return {
                "status": "INFO",
                "message": "Closing handled by reversing original trade."
            }

        else:
            return {"error": f"Unknown action: {action}"}

        # 5. Shares for each leg
        shares1 = value_leg1 / exec_p1
        shares2 = value_leg2 / exec_p2

        return {
            "status": "FILLED",
            "slippage_bps": slippage_bps,
            "hedge_ratio": hedge_ratio,
            "total_value": total_value,

            "leg1": {
                "ticker": ticker_leg1,
                "side": side1,
                "market_price": round(p1, 2),
                "avg_fill": round(exec_p1, 2),
                "shares": round(shares1, 4),
                "allocation_value": round(value_leg1, 2)
            },

            "leg2": {
                "ticker": ticker_leg2,
                "side": side2,
                "market_price": round(p2, 2),
                "avg_fill": round(exec_p2, 2),
                "shares": round(shares2, 4),
                "allocation_value": round(value_leg2, 2)
            }
        }

    except Exception as e:
        return {"error": str(e)}
