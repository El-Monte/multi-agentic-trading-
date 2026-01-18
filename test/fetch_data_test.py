"""
Test script for DataFetcher functionality with UTILITY PAIRS
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.data.fetch_data import DataFetcher
from src.analysis.cointegration import CointegrationAnalyzer

def test_fetch():
    """Test data fetching and analysis for Utility pairs."""
    
    print("="*60)
    print(" TESTING DATA PIPELINE: UTILITIES (ETR/AEP)")
    print("="*60)
    
    fetcher = DataFetcher(start_date="2023-01-01", end_date="2025-01-01")
    
    # Test 1: Single stock (ETR) 
    print("\n1. Testing single stock fetch (ETR)...")
    stock_data = fetcher.fetch_stock('ETR')
    
    print(f"   ETR data points: {len(stock_data)}")
    print(f"   Data type: {type(stock_data).__name__}")
    if not stock_data.empty:
        print(f"   ✅ Date range: {stock_data.index[0].date()} to {stock_data.index[-1].date()}")
    
    # Test 2: Pair fetch (ETR / AEP) 
    print("\n2. Testing pair fetch (ETR / AEP)...")
    pair = fetcher.fetch_pair('ETR', 'AEP')
    
    if pair.empty:
        print("   FAILED: Could not fetch pair data")
        return

    print(f"   Pair shape: {pair.shape}")
    print(f"   Columns: {pair.columns.tolist()}")
    
    # Test 3: Analysis 
    print("\n3. Testing cointegration analysis...")
    analyzer = CointegrationAnalyzer()
    
    result = analyzer.analyze_pair(
        pair, 
        'ETR', 
        'AEP'
    )

    print(f"   Pair calculated: ETR/AEP")
    print(f"   Correlation: {result['correlation']:.4f}")

    is_coint = result['eg_pvalue'] < 0.10
    print(f"   Cointegrated (p<0.10): {is_coint}")
    print(f"   Engle-Granger p-value: {result['eg_pvalue']:.6f}")
    print(f"   Half-life: {result['half_life']:.2f} days")
    print(f"   Hurst exponent: {result['hurst']:.4f}")
    
    # Test 4: Scoring 
    score = analyzer.score_pair(result)
    print(f"   Quality Score: {score:.1f}/100")

    print("\n" + "="*60)
    print(" SYSTEM READY FOR PAIR DISCOVERY")
    print("="*60)

if __name__ == "__main__":
    test_fetch()