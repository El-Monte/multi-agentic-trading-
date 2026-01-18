import sys
import os

# Ensure the system can find the src folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.execution_tools import execute_pairs_trade

print("="*60)
print("  TESTING EXECUTION SIMULATION (UTILITIES)")
print("="*60)

print("\n--- Scenario: OPEN SHORT on ETR/AEP ---")
print("Context: The spread between Entergy (ETR) and AEP is historically high (Z-Score > 2.5).")
print("Strategy: We expect the spread to shrink. We SELL ETR and BUY AEP.")

result = execute_pairs_trade.run(
    ticker_leg1="ETR", 
    ticker_leg2="AEP", 
    action="OPEN_SHORT", 
    total_value=10000, 
    hedge_ratio=0.98, 
    slippage_bps=10  
)

import json
print("\n Execution Result:")
print(json.dumps(result, indent=2))

print("\n" + "="*60)
print("LOGIC CHECK:")
print("1. Leg 1 (ETR) should be 'SELL'.")
print("2. Leg 2 (AEP) should be 'BUY'.")
print("3. Fill Price should include slippage (Buy > Market, Sell < Market).")
print("="*60)