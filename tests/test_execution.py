import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.execution_tools import execute_pairs_trade

print("--- Testing Execution Simulation ---")
# Scenario: Agent wants to OPEN SHORT on NEE/CWEN with $10,000
# "SHORT SPREAD" means: Spread is too high. SELL A, BUY B.

result = execute_pairs_trade.run(
    ticker_leg1="NEE", 
    ticker_leg2="CWEN", 
    action="SHORT_SPREAD", 
    total_value=10000, 
    hedge_ratio=0.948
)

print(result)

# Check logic:
# Leg 1 (NEE) should be "SELL"
# Leg 2 (CWEN) should be "BUY"
# avg_price for BUY should be > market_price (due to slippage)
# avg_price for SELL should be < market_price (due to slippage)