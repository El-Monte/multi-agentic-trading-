import yfinance as yf
import pandas as pd
from crewai.tools import tool
from typing import Dict, List, Union

@tool("Check Risk Limits")
def check_risk_limits(current_positions_value: float, new_trade_value: float, total_capital: float, max_leverage: float = 2.0) -> Dict:
    """
    Checks if a proposed trade violates portfolio leverage limits.
    
    Args:
        current_positions_value (float): Total market value (absolute) of all currently held positions.
        new_trade_value (float): The total $ value of the proposed new trade (Long + Short legs).
        total_capital (float): The total account equity (Cash + Positions).
        max_leverage (float): Maximum allowed leverage ratio (default 2.0).
        
    Returns:
        Dict: {'allowed': bool, 'reason': str, 'new_leverage': float}
    """
    try:
        # 1. Calculate Projected Exposure (Current + New)
        projected_exposure = current_positions_value + new_trade_value
        
        # 2. Calculate Leverage
        # Leverage = Total Exposure / Total Equity
        if total_capital == 0:
             return {"allowed": False, "reason": "Total capital is zero."}
             
        new_leverage = projected_exposure / total_capital
        
        # 3. Check Limit
        if new_leverage > max_leverage:
            return {
                "allowed": False,
                "reason": f"Leverage limit exceeded. Projected: {new_leverage:.2f}x > Max: {max_leverage}x",
                "current_leverage": round(current_positions_value / total_capital, 2),
                "new_leverage": round(new_leverage, 2)
            }
        
        return {
            "allowed": True,
            "reason": "Risk checks passed. Leverage within limits.",
            "new_leverage": round(new_leverage, 2)
        }
    except Exception as e:
        return {"allowed": False, "reason": f"Error: {str(e)}"}

@tool("Check Portfolio Correlation")
def check_correlation(new_ticker: str, existing_tickers: List[str], correlation_threshold: float = 0.85) -> Dict:
    """
    Checks if a new stock is too highly correlated with any stock currently in the portfolio.
    
    Args:
        new_ticker (str): The ticker symbol of the stock we want to trade.
        existing_tickers (List[str]): List of tickers we already hold positions in.
        correlation_threshold (float): Max allowed correlation (default 0.85).
    
    Returns:
        Dict: 
            - 'allowed': bool
            - 'max_correlation': float (The highest correlation found)
            - 'conflicting_ticker': str (The ticker it clashed with)
    """
    if not existing_tickers:
        return {"allowed": True, "max_correlation": 0.0, "reason": "Portfolio is empty."}
        
    try:
        # 1. Fetch Data for ALL tickers (New + Existing)
        all_tickers = existing_tickers + [new_ticker]
        # Join list into string for yfinance (e.g., "NEE CWEN RUN")
        tickers_str = " ".join(all_tickers)
        
        # Download 3 months of data
        data = yf.download(tickers_str, period="6mo", progress=False, auto_adjust=True)['Close']
        
        if data.empty:
             return {"allowed": False, "reason": "Failed to fetch price data."}

        # 2. Calculate Daily Returns (Percentage Change)
        # We look at correlation of RETURNS, not Prices (Prices are non-stationary)
        returns = data.pct_change().dropna()
        
        # 3. Check Correlation against the New Ticker
        # We only care about how 'new_ticker' correlates with the others
        corr_matrix = returns.corr()
        
        max_corr = -1.0
        conflict_ticker = None
        
        # Iterate through existing tickers to find the worst match
        for ticker in existing_tickers:
            if ticker in corr_matrix.columns and new_ticker in corr_matrix.columns:
                # Get correlation value
                corr_val = corr_matrix.loc[new_ticker, ticker]
                
                if corr_val > max_corr:
                    max_corr = corr_val
                    conflict_ticker = ticker
        
        # 4. Decision
        if max_corr > correlation_threshold:
            return {
                "allowed": False,
                "reason": f"High correlation detected with {conflict_ticker} ({max_corr:.2f}). Diversification required.",
                "max_correlation": round(max_corr, 2),
                "conflicting_ticker": conflict_ticker
            }
            
        return {
            "allowed": True,
            "reason": "Correlation check passed. Asset provides diversification.",
            "max_correlation": round(max_corr, 2)
        }

    except Exception as e:
        return {"error": str(e)}
