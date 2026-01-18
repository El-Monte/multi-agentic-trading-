from crewai.tools import tool
from typing import Dict

@tool("Calculate Position Size")
def calculate_position_size(total_capital: float, confidence_score: float, max_allocation_pct: float = 0.20) -> Dict:
    """
    Calculates the optimal $ amount to allocate to a trade using confidence-weighted sizing.
    
    This acts as a conservative wrapper around the Kelly Criterion. Instead of estimating 
    probabilities directly, it scales the maximum allowed position by the signal's 
    statistical confidence (derived from Z-score magnitude).
    
    Args:
        total_capital (float): Total available equity in the portfolio.
        confidence_score (float): The confidence of the signal (0.0 to 1.0).
        max_allocation_pct (float): The maximum % of capital allowed for a single pair (default 0.20 or 20%).
        
    Returns:
        Dict: 
            - 'allocation_amount': The calculated $ amount to trade.
            - 'allocation_pct': The calculated % of portfolio.
            - 'reason': Explanation of the sizing.
    """
    try:
        # 1. Safety Checks
        if confidence_score < 0 or confidence_score > 1.0:
            return {"error": "Confidence score must be between 0.0 and 1.0"}
        
        # 2. Calculate Base Allocation
        target_pct = max_allocation_pct * confidence_score
        allocation_amount = total_capital * target_pct
        
        # 3. Rounding for clean numbers
        allocation_amount = round(allocation_amount, 2)
        target_pct_display = round(target_pct * 100, 2)
        
        return {
            "allocation_amount": allocation_amount,
            "allocation_pct": f"{target_pct_display}%",
            "reason": f"Allocating {target_pct_display}% of capital based on {confidence_score*100:.0f}% signal confidence."
        }
    except Exception as e:
        return {"error": str(e)}

@tool("Calculate Kelly Criterion (Advanced)")
def calculate_kelly_allocation(win_probability: float, risk_reward_ratio: float, total_capital: float) -> Dict:
    """
    Calculates the strict Kelly Criterion percentage for a trade.
    Useful for theoretical checks based on historical win rates.
    
    Formula: f = p - (1-p)/b
    
    Args:
        win_probability (float): Probability of winning (e.g., 0.60 for 60%).
        risk_reward_ratio (float): Ratio of Avg Win / Avg Loss (e.g., 1.5).
        total_capital (float): Total equity.
    
    Returns:
        Dict: The optimal allocation amount and percentage.
    """
    try:
        q = 1 - win_probability
        kelly_pct = win_probability - (q / risk_reward_ratio)
        
        safe_kelly_pct = kelly_pct * 0.5
        
        if safe_kelly_pct < 0:
            safe_kelly_pct = 0.0
            
        allocation_amount = total_capital * safe_kelly_pct
        
        return {
            "kelly_fraction": round(safe_kelly_pct, 4),
            "allocation_amount": round(allocation_amount, 2),
            "explanation": "Calculated using Half-Kelly for safety."
        }
    except Exception as e:
        return {"error": str(e)}