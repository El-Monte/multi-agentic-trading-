import sys
import os

# Path Setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.risk_tools import check_risk_limits, check_correlation

print("--- 1. Testing Leverage Check ---")
# Case A: Safe
result_safe = check_risk_limits.run(
    current_positions_value=50000, 
    new_trade_value=10000, 
    total_capital=100000
)
print(f"Safe Trade: {result_safe['allowed']} (Lev: {result_safe['new_leverage']}x)")

# Case B: Dangerous (Over-leveraged)
result_danger = check_risk_limits.run(
    current_positions_value=190000, 
    new_trade_value=20000, 
    total_capital=100000
)
print(f"Dangerous Trade: {result_danger['allowed']} ({result_danger['reason']})")


print("\n--- 2. Testing Correlation Check ---")
# Case A: High Correlation (NEE vs CWEN are both Green Energy Utilities)
print("Checking NEE vs CWEN (Should likely FAIL or be High)...")
corr_result = check_correlation.run(
    new_ticker="CWEN",
    existing_tickers=["NEE"]
)
print(f"Result: {corr_result['allowed']} (Max Corr: {corr_result.get('max_correlation')})")

# Case B: Low Correlation (NEE vs SPY/Oil/Tech - let's try something different like 'XOM' - Exxon Mobil)
# Note: XOM is traditional energy, NEE is green. They might have lower correlation.
print("\nChecking XOM vs NEE...")
corr_result_2 = check_correlation.run(
    new_ticker="XOM",
    existing_tickers=["NEE"]
)
print(f"Result: {corr_result_2['allowed']} (Max Corr: {corr_result_2.get('max_correlation')})")