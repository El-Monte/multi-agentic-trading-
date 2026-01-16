import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.signal_tools import calculate_spread_and_zscore

# Test with Pair 1: ETR/AEP (Hedge Ratio: 0.948)
print("Testing ETR/AEP...")
result = calculate_spread_and_zscore.run(
    ticker_leg1="ETR", 
    ticker_leg2="AEP", 
    hedge_ratio=0.948, 
    lookback_window=20
)

print(result)