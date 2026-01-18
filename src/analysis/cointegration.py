"""
Cointegration testing and pair validation for statistical arbitrage.
"""

import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.tsa.stattools import adfuller, coint
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
from typing import Tuple, Dict
import warnings
warnings.filterwarnings('ignore')


class CointegrationAnalyzer:
    """Statistical tests for pairs trading validation."""
    
    @staticmethod
    def adf_test(series: pd.Series) -> Tuple[float, float]:
        """
        Augmented Dickey-Fuller test for stationarity.
        """
        result = adfuller(series.dropna(), autolag='AIC')
        return result[0], result[1]
    
    @staticmethod
    def engle_granger_test(stock_a: pd.Series, stock_b: pd.Series) -> Tuple[float, float]:
        """
        Engle-Granger two-step cointegration test.
        """
        result = coint(stock_a, stock_b)
        return result[0], result[1]
    
    @staticmethod
    def calculate_hedge_ratio(stock_a: pd.Series, stock_b: pd.Series) -> float:
        """
        OLS regression to find optimal hedge ratio.
        """
        X = add_constant(stock_b)
        model = OLS(stock_a, X).fit()
        return model.params[1]
    
    @staticmethod
    def calculate_spread(stock_a: pd.Series, stock_b: pd.Series, hedge_ratio: float) -> pd.Series:
        """
        Calculate the spread: stock_a - hedge_ratio * stock_b
        """
        return stock_a - hedge_ratio * stock_b
    
    @staticmethod
    def half_life(spread: pd.Series) -> float:
        """
        Calculate mean reversion half-life via AR(1) model.
        
        Returns:
            Half-life in days (lower = faster mean reversion)
        """
        spread_clean = spread.dropna()
        
        if len(spread_clean) < 20:
            return np.inf
        
        spread_lag = spread_clean.shift(1).dropna()
        spread_diff = spread_clean.diff().dropna()
        
        common_index = spread_lag.index.intersection(spread_diff.index)
        spread_lag = spread_lag.loc[common_index]
        spread_diff = spread_diff.loc[common_index]
        
        if len(spread_lag) < 10:
            return np.inf
        
        try:
            # AR(1) regression: Δspread_t = λ * spread_{t-1}
            X = spread_lag.values.reshape(-1, 1)
            y = spread_diff.values
            
            # OLS estimate
            beta = np.linalg.lstsq(X, y, rcond=None)[0][0]
            
            # Must be negative for mean reversion
            if beta >= 0:
                return np.inf
            
            # Half-life calculation
            half_life_val = -np.log(2) / beta
            
            # Sanity checks
            if half_life_val <= 0 or half_life_val > 500 or not np.isfinite(half_life_val):
                return np.inf
            
            return half_life_val
            
        except Exception as e:
            return np.inf
    
    @staticmethod
    def hurst_exponent(series: pd.Series) -> float:
        """
        Calculate Hurst exponent to test mean reversion.
        
        Returns:
            H < 0.5 → mean-reverting
            H = 0.5 → random walk
            H > 0.5 → trending
        """
        try:
            lags = range(2, min(100, len(series)//2))
            tau = [np.std(np.subtract(series[lag:].values, series[:-lag].values)) for lag in lags]
            
            tau = [t for t in tau if t > 0 and np.isfinite(t)]
            if len(tau) < 10:
                return 0.5
            
            poly = np.polyfit(np.log(lags[:len(tau)]), np.log(tau), 1)
            return poly[0]
        except:
            return 0.5
    
    def analyze_pair(self, data: pd.DataFrame, ticker_a: str, ticker_b: str) -> Dict:
        """
        Comprehensive analysis of a potential pair.
        Args:
            data: DataFrame with columns [ticker_a, ticker_b]
            ticker_a: Symbol 1
            ticker_b: Symbol 2
        """
        try:
            stock_a = data[ticker_a]
            stock_b = data[ticker_b]

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
                'score': None
            }
        except Exception as e:
            return {
                'pair': f"{ticker_a}/{ticker_b}",
                'correlation': 0.0,
                'eg_statistic': 0.0,
                'eg_pvalue': 1.0,
                'cointegrated': False,
                'hedge_ratio': 0.0,
                'adf_statistic': 0.0,
                'adf_pvalue': 1.0,
                'spread_stationary': False,
                'half_life': np.inf,
                'hurst': 0.5,
                'mean_reverting': False,
                'spread_mean': 0.0,
                'spread_std': 0.0,
                'score': 0.0
            }
    
    @staticmethod
    def score_pair(result: Dict) -> float:
        """
        Composite score for ranking pairs (higher = better).
        """
        score = 0.0
        
        # Cointegration score 
        if result['eg_pvalue'] < 0.01:
            score += 50
        elif result['eg_pvalue'] < 0.05:
            score += 30
        elif result['eg_pvalue'] < 0.10:
            score += 20
        
        # Mean reversion score
        if result['hurst'] < 0.4 and result['half_life'] < 30:
            score += 30
        elif result['hurst'] < 0.5 and result['half_life'] < 60:
            score += 20
        elif result['hurst'] < 0.6 and result['half_life'] < 120:
            score += 10
        
        # Correlation score 
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
    """
    results = []
    
    total_pairs = len(stocks_a) * len(stocks_b)
    count = 0
    
    for ticker_a in stocks_a:
        for ticker_b in stocks_b:
            if ticker_a == ticker_b:
                continue
            
            count += 1
            print(f"Testing {count}/{total_pairs-len(stocks_a)}: {ticker_a}/{ticker_b}...", end='\r')
            
            try:
                data = fetcher.fetch_pair(ticker_a, ticker_b)
                
                if len(data) < 500:
                    continue
                
                result = analyzer.analyze_pair(
                    data[ticker_a], data[ticker_b], 
                    ticker_a, ticker_b
                )
                
                result['score'] = analyzer.calculate_pair_score(result)
                
                results.append(result)
                
            except Exception as e:
                continue
    
    print("\nScreening complete!" + " "*50)
    
    if len(results) == 0:
        return pd.DataFrame()
    
    df = pd.DataFrame(results)
    df = df.sort_values('score', ascending=False).reset_index(drop=True)
    
    return df