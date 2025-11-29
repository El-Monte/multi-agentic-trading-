import yfinance as yf
import pandas as pd
import numpy as np
from crewai.tools import tool
from typing import Dict, Union

# Set up logging or simple print for debugging
def log_error(msg):
    print(f"[ERROR] {msg}")

@tool("Calculate Spread and Z-Score")
def calculate_spread_and_zscore(ticker_leg1: str, ticker_leg2: str, hedge_ratio: float, lookback_window: int = 20) -> Dict:
    """
    Calculates the current spread and Z-score for a given pair of stocks.
    
    This tool fetches the latest market data, computes the spread based on the 
    provided hedge ratio, and normalizes it into a Z-score using a rolling window.
    
    Args:
        ticker_leg1 (str): Ticker symbol for the first stock (Leg A).
        ticker_leg2 (str): Ticker symbol for the second stock (Leg B).
        hedge_ratio (float): The hedge ratio (beta) derived from cointegration analysis.
        lookback_window (int): Number of days for rolling mean/std dev calculation. Default is 20.
        
    Returns:
        Dict: Contains:
            - 'z_score': The current Z-score (float).
            - 'spread': The current raw spread value (float).
            - 'leg1_price': Latest close price of Leg 1.
            - 'leg2_price': Latest close price of Leg 2.
            - 'mean': Current rolling mean of spread.
            - 'std': Current rolling std dev of spread.
            
    Example:
        result = calculate_spread_and_zscore("NEE", "CWEN", 0.948, 20)
    """
    try:
        # 1. Fetch Data
        # We need enough data for the lookback window + some buffer. 
        # Fetching 3 months ensures we have plenty of days for a 20-day window.
        tickers = f"{ticker_leg1} {ticker_leg2}"
        data = yf.download(tickers, period="3mo", progress=False)['Close']
        
        # Check if data is empty or missing columns
        if data.empty or ticker_leg1 not in data.columns or ticker_leg2 not in data.columns:
            return {"error": f"Failed to fetch data for {ticker_leg1} or {ticker_leg2}"}

        # 2. Extract Series
        leg1_prices = data[ticker_leg1]
        leg2_prices = data[ticker_leg2]

        # 3. Calculate Spread
        # Formula: Spread = Leg1 - (Hedge_Ratio * Leg2)
        spread_series = leg1_prices - (hedge_ratio * leg2_prices)

        # 4. Calculate Rolling Statistics
        # We use standard rolling window to avoid look-ahead bias
        rolling_mean = spread_series.rolling(window=lookback_window).mean()
        rolling_std = spread_series.rolling(window=lookback_window).std()

        # 5. Calculate Z-Score
        # Formula: Z = (Spread - Mean) / Std
        z_score_series = (spread_series - rolling_mean) / rolling_std

        # 6. Get the most recent values (the "Live" values)
        latest_z = z_score_series.iloc[-1]
        latest_spread = spread_series.iloc[-1]
        
        # Handle NaN (can happen if not enough data points for window)
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
        return {"error": str(e)}
    

@tool("Generate Trade Signal")
def generate_trade_signal(z_score: float, entry_threshold: float = 2.5, exit_threshold: float = 0.5, stop_loss_threshold: float = 4.0) -> Dict:
    """
    Analyzes the Z-score to generate a trading signal based on mean reversion logic.
    Includes a 'Stop Loss' mechanism to close positions if the spread diverges too far.
    
    Args:
        z_score (float): The current Z-score.
        entry_threshold (float): Z-score to enter trade (default 2.5).
        exit_threshold (float): Z-score to exit trade profitably (default 0.5).
        stop_loss_threshold (float): Z-score to Panic Close to prevent blowups (default 4.0).
    
    Returns:
        Dict: Signal, confidence, and reason.
    """
    # 1. STOP LOSS CHECK (Priority #1)
    if abs(z_score) > stop_loss_threshold:
        return {
            "signal": "CLOSE",
            "confidence": 1.0,
            "reason": f"STOP LOSS TRIGGERED. Z-score {z_score} exceeded safety limit {stop_loss_threshold}. Variance is exploding.",
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
            "entry": entry_threshold, 
            "exit": exit_threshold,
            "stop_loss": stop_loss_threshold
        }
    }