import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.risk_tools import check_risk_limits, check_correlation

print("="*60)
print("  TESTING RISK MANAGEMENT TOOLS (UTILITY SECTOR)")
print("="*60)

print("\n--- 1. Testing Leverage Check ---")
# Case A: Safe Trade
# We have $50k used, adding $10k. Total $60k / $100k equity = 0.6x Leverage. Safe.
result_safe = check_risk_limits.run(
    current_positions_value=50000, 
    new_trade_value=10000, 
    total_capital=100000
)
print(f" Safe Trade: {result_safe['allowed']} (Lev: {result_safe['new_leverage']}x)")

# Case B: Dangerous Trade
# We have $190k used (already leveraged), adding $20k. Total $210k / $100k = 2.1x. Danger.
result_danger = check_risk_limits.run(
    current_positions_value=190000, 
    new_trade_value=20000, 
    total_capital=100000
)
print(f" Dangerous Trade: {result_danger['allowed']} ({result_danger['reason']})")


print("\n--- 2. Testing Portfolio Correlation Check ---")
print("Checking relationships between ETR, AEP, and ATO.")

# Case A: Extremely High Correlation (Risk Rejection)
# ETR vs AEP are both large Electric Utilities. Correlation is usually > 0.95.
print("\n👉 Checking adding AEP to a portfolio holding ETR...")
corr_result = check_correlation.run(
    new_ticker="AEP",
    existing_tickers=["ETR"],
    correlation_threshold=0.90 
)
print(f"   Result: {corr_result['allowed']}")
print(f"   Details: Max Correlation is {corr_result.get('max_correlation')} (Likely Rejected - Too Concentrated)")

print("\n Checking adding ATO (Gas) to a portfolio holding ETR (Electric)...")
corr_result_2 = check_correlation.run(
    new_ticker="ATO",
    existing_tickers=["ETR"],
    correlation_threshold=0.95 
)
print(f"   Result: {corr_result_2['allowed']}")
print(f"   Details: Max Correlation is {corr_result_2.get('max_correlation')}")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)