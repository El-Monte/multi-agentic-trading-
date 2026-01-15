import yfinance as yf
import pandas as pd
import numpy as np
from crewai.tools import tool
from typing import Dict

@tool("Calculate Spread and Z-Score")
def calculate_spread_and_zscore(ticker_leg1: str, ticker_leg2: str, lookback_window: int = 20) -> Dict:
    """
    Calculates the current spread and Z-score using a dynamic Rolling Hedge Ratio.
    """
    try:
        # Fetch 6 months to have enough data for the 60-day rolling beta
        data = yf.download(f"{ticker_leg1} {ticker_leg2}", period="6mo", progress=False)['Close']
        if data.empty: return {"error": "No data"}
        
        df = data[[ticker_leg1, ticker_leg2]].dropna()
        
        # 1. Dynamic Rolling Beta (Hedge Ratio) - Last 60 days
        window_beta = 60
        rolling_cov = df[ticker_leg1].rolling(window=window_beta).cov(df[ticker_leg2])
        rolling_var = df[ticker_leg2].rolling(window=window_beta).var()
        df['Dynamic_Beta'] = rolling_cov / rolling_var
        
        # 2. Calculate Spread using YESTERDAY'S Beta to avoid leakage
        df['Spread'] = df[ticker_leg1] - (df['Dynamic_Beta'].shift(1) * df[ticker_leg2])
        
        # 3. Z-Score logic
        df['Mean'] = df['Spread'].rolling(window=lookback_window).mean()
        df['Std'] = df['Spread'].rolling(window=lookback_window).std()
        df['Z_Score'] = (df['Spread'] - df['Mean']) / df['Std']
        
        latest = df.iloc[-1]
        if pd.isna(latest['Z_Score']): return {"error": "NaN Z-score"}

        return {
            "z_score": float(round(latest['Z_Score'], 4)),
            "current_hedge_ratio": float(round(latest['Dynamic_Beta'], 4)),
            "spread": float(round(latest['Spread'], 4)),
            "leg1_price": float(round(latest[ticker_leg1], 2)),
            "leg2_price": float(round(latest[ticker_leg2], 2))
        }
    except Exception as e:
        return {"error": str(e)}

@tool("Generate Trade Signal")
def generate_trade_signal(z_score: float) -> Dict:
    """
    Analyzes the Z-score to generate a trading signal based on mean reversion logic.
    Uses fixed thresholds: Entry=2.5, Exit=0.5, Stop=4.0.
    
    Args:
        z_score (float): The current Z-score.
    """
    # HARDCODED DEFAULTS (Simpler for the Agent)
    entry_threshold = 2.5
    exit_threshold = 0.5
    stop_loss_threshold = 4.0

    # 1. STOP LOSS CHECK
    if abs(z_score) > stop_loss_threshold:
        return {
            "signal": "CLOSE",
            "confidence": 1.0,
            "reason": f"STOP LOSS TRIGGERED. Z-score {z_score} exceeded safety limit {stop_loss_threshold}.",
            "parameters": {"z_score": z_score, "stop_loss": True}
        }
        
    # 2. Normal Logic
    signal = "HOLD"
    reason = f"Z-score {z_score} is within neutral bounds."
    
    if z_score > entry_threshold:
        signal = "OPEN_SHORT"
        reason = f"Z-score {z_score} > {entry_threshold}. Overbought."
    elif z_score < -entry_threshold:
        signal = "OPEN_LONG"
        reason = f"Z-score {z_score} < -{entry_threshold}. Oversold."
    elif abs(z_score) < exit_threshold:
        signal = "CLOSE"
        reason = f"Z-score {z_score} returned to mean."

    # 3. Confidence Calculation
    excess = max(0, abs(z_score) - entry_threshold)
    if signal in ["OPEN_LONG", "OPEN_SHORT"]:
        confidence = min(1.0, 0.6 + (excess * 0.4))
    elif signal == "CLOSE":
        confidence = 1.0
    else:
        confidence = 0.0
        
    return {
        "signal": signal,
        "confidence": float(round(confidence, 2)),
        "reason": reason,
        "parameters": {
            "z_score": z_score, 
            "thresholds": "Fixed (2.5/0.5/4.0)"
        }
    }
