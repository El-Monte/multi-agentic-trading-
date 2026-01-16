import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.signal_tools import calculate_spread_and_zscore, generate_trade_signal

print("="*60)
print("📡 TESTING SIGNAL LOGIC (UTILITIES)")
print("="*60)

print("\n--- 1. Testing Live Data (Integration) ---")
print("Target: Entergy (ETR) vs American Electric Power (AEP)")

# 1. Get the live Z-score first
# 👇 FIX: Removed 'hedge_ratio'. The tool calculates it dynamically now.
live_data = calculate_spread_and_zscore.run(
    ticker_leg1="ETR", 
    ticker_leg2="AEP",
    lookback_window=20
)

# 2. Extract Z-score safely
if isinstance(live_data, dict) and 'error' in live_data:
    print(f"❌ Error fetching data: {live_data['error']}")
else:
    # Handle case where tool might return string or dict
    if isinstance(live_data, str):
        print(f"⚠️ Raw output received (might be error): {live_data}")
        z = 0.0
    else:
        z = live_data.get('z_score', 0.0)
        curr_hedge = live_data.get('current_hedge_ratio', 'N/A')
        
        print(f"✅ Live Z-Score for ETR/AEP: {z}")
        print(f"   Calculated Hedge Ratio: {curr_hedge}")

        # 3. Generate signal based on live data
        # Note: We rely on defaults for thresholds
        decision = generate_trade_signal.run(z_score=z)
        
        print(f"   Agent Decision: {decision.get('signal')} ({decision.get('reason')})")


print("\n--- 2. Testing Scenarios (Unit Tests) ---")
print("Checking if logic holds for extreme values:")

# Scenario A: Extreme High Z-Score (Should be OPEN_SHORT)
res_a = generate_trade_signal.run(z_score=3.0)
print(f"Scenario A (Z=3.0):  {res_a.get('signal')}  (Expected: OPEN_SHORT)")

# Scenario B: Extreme Low Z-Score (Should be OPEN_LONG)
res_b = generate_trade_signal.run(z_score=-2.8)
print(f"Scenario B (Z=-2.8): {res_b.get('signal')}   (Expected: OPEN_LONG)")

# Scenario C: Normal Z-Score (Should be CLOSE or HOLD)
res_c = generate_trade_signal.run(z_score=0.1)
print(f"Scenario C (Z=0.1):  {res_c.get('signal')}        (Expected: HOLD or CLOSE)")

print("\n" + "="*60)