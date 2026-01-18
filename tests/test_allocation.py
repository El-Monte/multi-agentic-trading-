import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.allocation_tools import calculate_position_size, calculate_kelly_allocation

print("="*60)
print(" TESTING CAPITAL ALLOCATION (UTILITY SECTOR)")
print("="*60)

print("\n--- 1. Testing Confidence Sizing (ETR/AEP Example) ---")

# Scenario A: ETR/AEP has a Z-Score > 2.5 and Bullish Sentiment
res_strong = calculate_position_size.run(
    total_capital=100000, 
    confidence_score=0.8, 
    max_allocation_pct=0.20
)
print(f" ETR/AEP Strong Signal (0.8): ${res_strong.get('allocation_amount')} ({res_strong.get('allocation_pct')})")

# Scenario B: AEP/ATO has a Z-Score barely > 2.0 and Neutral Sentiment
res_weak = calculate_position_size.run(
    total_capital=100000, 
    confidence_score=0.2, 
    max_allocation_pct=0.20
)
print(f" AEP/ATO Weak Signal   (0.2): ${res_weak.get('allocation_amount')} ({res_weak.get('allocation_pct')})")


print("\n--- 2. Testing Kelly Criterion (Theoretical Check) ---")
kelly = calculate_kelly_allocation.run(
    win_probability=0.65,
    risk_reward_ratio=1.2,
    total_capital=100000
)
print(f" Kelly Suggestion for Utilities: ${kelly.get('allocation_amount')} (Approx {kelly.get('kelly_fraction')*100:.1f}%)")
print(f"   Reason: {kelly.get('explanation')}")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)