import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.signal_tools import calculate_spread_and_zscore, generate_trade_signal

print("--- 1. Testing Live Data (Integration) ---")
# Get the live Z-score first
live_data = calculate_spread_and_zscore.run(
    ticker_leg1="ETR", ticker_leg2="AEP", hedge_ratio=0.948
)
z = live_data['z_score']
print(f"Live Z-Score for ETR/AEP: {z}")

# Generate signal based on live data
decision = generate_trade_signal.run(z_score=z)
print(f"Agent Decision: {decision['signal']} ({decision['reason']})")


print("\n--- 2. Testing Scenarios (Unit Tests) ---")
# Scenario A: Extreme High Z-Score (Should be OPEN_SHORT)
print("Scenario A (Z=3.0):", generate_trade_signal.run(z_score=3.0)['signal'])

# Scenario B: Extreme Low Z-Score (Should be OPEN_LONG)
print("Scenario B (Z=-2.8):", generate_trade_signal.run(z_score=-2.8)['signal'])

# Scenario C: Normal Z-Score (Should be CLOSE or HOLD)
print("Scenario C (Z=0.1):", generate_trade_signal.run(z_score=0.1)['signal'])