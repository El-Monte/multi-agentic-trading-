import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.signal_tools import calculate_spread_and_zscore

print("="*60)
print(" TESTING SIGNAL GENERATION (UTILITY PAIR)")
print("="*60)

# Test: ETR/AEP
print("\nTesting ETR (Entergy) / AEP (American Electric Power)...")
print("Using Dynamic Hedge Ratio (Tool calculates beta automatically)")

result = calculate_spread_and_zscore.run(
    ticker_leg1="ETR", 
    ticker_leg2="AEP", 
    lookback_window=20
)

print("\n Result:")
print(json.dumps(result, indent=2))

print("\n" + "="*60)
print("LOGIC CHECK:")
print("1. Did it fetch prices?")
print("2. Is 'current_hedge_ratio' visible in the output?")
print("3. Is the Z-Score calculated?")
print("="*60)