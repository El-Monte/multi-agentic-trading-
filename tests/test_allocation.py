import sys
import os

# Path Setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.allocation_tools import calculate_position_size, calculate_kelly_allocation

print("--- 1. Testing Confidence Sizing ---")

# Scenario A: Strong Signal (80% Confidence)
# We expect: $100,000 * 20% Max * 0.8 Confidence = $16,000
res_strong = calculate_position_size.run(
    total_capital=100000, 
    confidence_score=0.8, 
    max_allocation_pct=0.20
)
print(f"Strong Signal (0.8): ${res_strong.get('allocation_amount')} ({res_strong.get('allocation_pct')})")

# Scenario B: Weak Signal (20% Confidence)
# We expect: $100,000 * 20% Max * 0.2 Confidence = $4,000
res_weak = calculate_position_size.run(
    total_capital=100000, 
    confidence_score=0.2, 
    max_allocation_pct=0.20
)
print(f"Weak Signal   (0.2): ${res_weak.get('allocation_amount')} ({res_weak.get('allocation_pct')})")


print("\n--- 2. Testing Kelly Criterion ---")
# Scenario: 60% Win Rate, 1.5 Risk/Reward
# This is a standard check to see what the math says "theoretically"
kelly = calculate_kelly_allocation.run(
    win_probability=0.6,
    risk_reward_ratio=1.5,
    total_capital=100000
)
print(f"Kelly Suggestion:    ${kelly.get('allocation_amount')} (Approx {kelly.get('kelly_fraction')*100:.1f}%)")