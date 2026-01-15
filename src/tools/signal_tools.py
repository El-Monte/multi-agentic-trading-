import yfinance as yf
import pandas as pd
import numpy as np
from crewai.tools import tool
from typing import Dict

@tool("Calculate Spread and Z-Score")
def calculate_spread_and_zscore(ticker_leg1: str, ticker_leg2: str, hedge_ratio: float, lookback_window: int = 20) -> Dict:
    """
    Calculates the current spread and Z-score for a given pair of stocks.
    Args:
        ticker_leg1 (str): Ticker symbol for the first stock (Leg A).
        ticker_leg2 (str): Ticker symbol for the second stock (Leg B).
        hedge_ratio (float): The hedge ratio (beta) derived from cointegration analysis.
        lookback_window (int): Number of days for rolling mean/std dev calculation. Default is 20.
    """
    try:
        # 1. Fetch Data
        tickers = f"{ticker_leg1} {ticker_leg2}"
        data = yf.download(tickers, period="3mo", progress=False)['Close']
        
        if data.empty:
            return {"error": f"Failed to fetch data for {tickers}"}
            
        if ticker_leg1 not in data.columns or ticker_leg2 not in data.columns:
            return {"error": f"Columns for {ticker_leg1} or {ticker_leg2} not found."}

        # 2. Extract Series
        leg1_prices = data[ticker_leg1]
        leg2_prices = data[ticker_leg2]

        # 3. Calculate Spread
        spread_series = leg1_prices - (hedge_ratio * leg2_prices)

        # 4. Calculate Rolling Statistics
        rolling_mean = spread_series.rolling(window=lookback_window).mean()
        rolling_std = spread_series.rolling(window=lookback_window).std()

        # 5. Calculate Z-Score
        z_score_series = (spread_series - rolling_mean) / rolling_std

        # 6. Get the most recent values
        latest_z = z_score_series.iloc[-1]
        latest_spread = spread_series.iloc[-1]
        
        if pd.isna(latest_z):
            return {"error": "Not enough data to calculate Z-score (NaN result)"}

        return {
            "z_score": float(round(latest_z, 4)),
            "spread": float(round(latest_spread, 4)),
            "leg1_price": float(round(leg1_prices.iloc[-1], 2)),
            "leg2_price": float(round(leg2_prices.iloc[-1], 2)),
            "rolling_mean": float(round(rolling_mean.iloc[-1], 4)),
            "rolling_std": float(round(rolling_std.iloc[-1], 4))
        }

    except Exception as e:
        return {"error": f"Calculation failed: {str(e)}"}

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