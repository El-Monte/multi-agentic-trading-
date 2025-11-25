"""
Cointegration testing and pair validation for statistical arbitrage.
"""

import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.tsa.stattools import adfuller, coint
from statsmodels.regression.linear_model import OLS
from typing import Tuple, Dict
import warnings
warnings.filterwarnings('ignore')


class CointegrationAnalyzer:
    """Statistical tests for pairs trading validation."""
    
    @staticmethod
    def adf_test(series: pd.Series) -> Tuple[float, float]:
        """
        Augmented Dickey-Fuller test for stationarity.
        
        Args:
            series: Time series to test
        
        Returns:
            (test_statistic, p_value)
            p_value < 0.05 → stationary (good for spreads)
        """
        result = adfuller(series.dropna(), autolag='AIC')
        return result[0], result[1]
    
    @staticmethod
    def engle_granger_test(stock_a: pd.Series, stock_b: pd.Series) -> Tuple[float, float]:
        """
        Engle-Granger two-step cointegration test.
        
        Args:
            stock_a: Price series for first stock
            stock_b: Price series for second stock
        
        Returns:
            (test_statistic, p_value)
            p_value < 0.05 → cointegrated (good pair)
        """
        result = coint(stock_a, stock_b)
        return result[0], result[1]
    
    @staticmethod
    def calculate_hedge_ratio(stock_a: pd.Series, stock_b: pd.Series) -> float:
        """
        OLS regression to find optimal hedge ratio.
        
        Args:
            stock_a: Dependent variable (Y)
            stock_b: Independent variable (X)
        
        Returns:
            Beta coefficient (units of stock_b per unit of stock_a)
        """
        model = OLS(stock_a, stock_b).fit()
        return model.params[0]
    
    @staticmethod
    def calculate_spread(stock_a: pd.Series, stock_b: pd.Series, hedge_ratio: float) -> pd.Series:
        """
        Calculate the spread: stock_a - hedge_ratio * stock_b
        
        Args:
            stock_a: First stock price
            stock_b: Second stock price
            hedge_ratio: Multiplier for stock_b
        
        Returns:
            Spread series
        """
        return stock_a - hedge_ratio * stock_b
    
    @staticmethod
    def half_life(spread: pd.Series) -> float:
        """
        Calculate mean reversion half-life via AR(1) model.
        
        Args:
            spread: Spread time series
        
        Returns:
            Half-life in days (lower = faster mean reversion)
        """
        spread_lag = spread.shift(1).dropna()
        spread_diff = spread.diff().dropna()
        
        # Align series
        spread_lag = spread_lag[spread_diff.index]
        
        # AR(1): Δspread = λ * spread_lag + ε
        model = OLS(spread_diff, spread_lag).fit()
        lambda_coef = model.params[0]
        
        if lambda_coef >= 0:
            return np.inf  # Not mean-reverting
        
        half_life = -np.log(2) / lambda_coef
        return half_life
    
    @staticmethod
    def hurst_exponent(series: pd.Series) -> float:
        """
        Calculate Hurst exponent to test mean reversion.
        
        Args:
            series: Time series
        
        Returns:
            H < 0.5 → mean-reverting
            H = 0.5 → random walk
            H > 0.5 → trending
        """
        lags = range(2, 100)
        tau = [np.std(np.subtract(series[lag:].values, series[:-lag].values)) for lag in lags]
        
        # Linear regression of log(tau) vs log(lag)
        poly = np.polyfit(np.log(lags), np.log(tau), 1)
        return poly[0]
    
    def analyze_pair(self, stock_a: pd.Series, stock_b: pd.Series, 
                    ticker_a: str, ticker_b: str) -> Dict:
        """
        Comprehensive analysis of a potential pair.
        
        Args:
            stock_a: First stock prices
            stock_b: Second stock prices
            ticker_a: First stock symbol
            ticker_b: Second stock symbol
        
        Returns:
            Dictionary with all test results
        """
        # Correlation
        correlation = stock_a.corr(stock_b)
        
        # Cointegration
        eg_stat, eg_pvalue = self.engle_granger_test(stock_a, stock_b)
        
        # Hedge ratio and spread
        hedge_ratio = self.calculate_hedge_ratio(stock_a, stock_b)
        spread = self.calculate_spread(stock_a, stock_b, hedge_ratio)
        
        # Spread stationarity
        adf_stat, adf_pvalue = self.adf_test(spread)
        
        # Mean reversion metrics
        half_life_days = self.half_life(spread)
        hurst = self.hurst_exponent(spread)
        
        # Spread statistics
        spread_mean = spread.mean()
        spread_std = spread.std()
        
        return {
            'pair': f"{ticker_a}/{ticker_b}",
            'correlation': correlation,
            'eg_statistic': eg_stat,
            'eg_pvalue': eg_pvalue,
            'cointegrated': eg_pvalue < 0.05,
            'hedge_ratio': hedge_ratio,
            'adf_statistic': adf_stat,
            'adf_pvalue': adf_pvalue,
            'spread_stationary': adf_pvalue < 0.05,
            'half_life': half_life_days,
            'hurst': hurst,
            'mean_reverting': hurst < 0.5,
            'spread_mean': spread_mean,
            'spread_std': spread_std,
            'score': None  # Will calculate composite score
        }
    
    @staticmethod
    def calculate_pair_score(result: Dict) -> float:
        """
        Composite score for ranking pairs (higher = better).
        
        Scoring criteria:
        - Cointegration (50%): Lower p-value is better
        - Mean reversion (30%): Lower Hurst, shorter half-life
        - Correlation (20%): Higher correlation
        """
        score = 0.0
        
        # Cointegration score (0-50 points)
        if result['eg_pvalue'] < 0.01:
            score += 50
        elif result['eg_pvalue'] < 0.05:
            score += 30
        else:
            score += 0
        
        # Mean reversion score (0-30 points)
        if result['hurst'] < 0.4 and result['half_life'] < 30:
            score += 30
        elif result['hurst'] < 0.5 and result['half_life'] < 60:
            score += 20
        elif result['hurst'] < 0.5:
            score += 10
        
        # Correlation score (0-20 points)
        if result['correlation'] > 0.8:
            score += 20
        elif result['correlation'] > 0.7:
            score += 15
        elif result['correlation'] > 0.6:
            score += 10
        
        return score


def screen_all_pairs(stocks_a: list, stocks_b: list, fetcher, analyzer) -> pd.DataFrame:
    """
    Test all possible pairs from two lists of stocks.
    
    Args:
        stocks_a: First list of tickers
        stocks_b: Second list of tickers
        fetcher: DataFetcher instance
        analyzer: CointegrationAnalyzer instance
    
    Returns:
        DataFrame with results sorted by score
    """
    results = []
    
    total_pairs = len(stocks_a) * len(stocks_b)
    count = 0
    
    for ticker_a in stocks_a:
        for ticker_b in stocks_b:
            if ticker_a == ticker_b:
                continue
            
            count += 1
            print(f"Testing {count}/{total_pairs}: {ticker_a}/{ticker_b}...", end='\r')
            
            try:
                # Fetch data
                data = fetcher.fetch_pair(ticker_a, ticker_b)
                
                if len(data) < 500:  # Need enough data
                    continue
                
                # Analyze pair
                result = analyzer.analyze_pair(
                    data[ticker_a], data[ticker_b], 
                    ticker_a, ticker_b
                )
                
                # Calculate score
                result['score'] = analyzer.calculate_pair_score(result)
                
                results.append(result)
                
            except Exception as e:
                print(f"\nError with {ticker_a}/{ticker_b}: {e}")
                continue
    
    print("\nScreening complete!")
    
    # Convert to DataFrame and sort
    df = pd.DataFrame(results)
    df = df.sort_values('score', ascending=False).reset_index(drop=True)
    
    return df