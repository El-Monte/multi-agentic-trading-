"""
Test script for DataFetcher functionality
"""

import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.data.Data_Fetcher import DataFetcher
from src.analysis.cointegration import CointegrationAnalyzer

def test_fetch():
    """Test data fetching and analysis."""
    
    print("="*60)
    print("TESTING DATA FETCHER")
    print("="*60)
    
    # Initialize
    fetcher = DataFetcher(start_date="2020-01-01", end_date="2024-01-01")
    
    # Test 1: Single stock
    print("\n1. Testing single stock fetch (XOM)...")
    xom = fetcher.fetch_stock('XOM')
    print(f"   ✅ XOM data points: {len(xom)}")
    print(f"   ✅ Data type: {type(xom).__name__}")
    print(f"   ✅ Date range: {xom.index[0]} to {xom.index[-1]}")
    
    # Test 2: Pair fetch
    print("\n2. Testing pair fetch (XOM/CVX)...")
    pair = fetcher.fetch_pair('XOM', 'CVX')
    
    if pair.empty:
        print("   ❌ FAILED: Could not fetch pair data")
        return
    
    print(f"   ✅ Pair shape: {pair.shape}")
    print(f"   ✅ Columns: {pair.columns.tolist()}")
    print(f"   ✅ First date: {pair.index[0]}")
    print(f"   ✅ Last date: {pair.index[-1]}")
    
    # Test 3: Analysis
    print("\n3. Testing cointegration analysis...")
    analyzer = CointegrationAnalyzer()
    
    result = analyzer.analyze_pair(
        pair['XOM'], 
        pair['CVX'], 
        'XOM', 
        'CVX'
    )
    
    print(f"   ✅ Pair: {result['pair']}")
    print(f"   ✅ Correlation: {result['correlation']:.4f}")
    print(f"   ✅ Cointegrated: {result['cointegrated']}")
    print(f"   ✅ Engle-Granger p-value: {result['eg_pvalue']:.6f}")
    print(f"   ✅ Half-life: {result['half_life']:.2f} days")
    print(f"   ✅ Hurst exponent: {result['hurst']:.4f}")
    
    # Calculate score
    score = analyzer.calculate_pair_score(result)
    print(f"   ✅ Score: {score:.1f}/100")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print("\nYou're ready to run the full pair discovery script.")
    print("Run: python src/pair_discovery.py")

if __name__ == "__main__":
    test_fetch()
