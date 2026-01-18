"""
Data fetching utilities for pairs trading analysis.
Downloads adjusted price data from Yahoo Finance.
"""

import yfinance as yf
import pandas as pd
from typing import List, Tuple
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class DataFetcher:
    """Fetch and prepare stock data for pairs analysis."""
    
    def __init__(self, start_date: str = "2015-01-01", end_date: str = "2023-01-01"):
        self.start_date = start_date
        self.end_date = end_date
    
    def fetch_stock(self, ticker: str) -> pd.Series:
        """
        Download adjusted close price for a single stock.
        
        Args:
            ticker: Stock symbol (e.g., 'XOM')
        
        Returns:
            Series with adjusted close prices
        """
        try:
            stock = yf.Ticker(ticker)
            data = stock.history(start=self.start_date, end=self.end_date, auto_adjust=True)
            
            if data.empty or len(data) < 100:
                return pd.Series(dtype=float)
            
            return data['Close']
            
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return pd.Series(dtype=float)
    
    def fetch_pair(self, ticker_a: str, ticker_b: str) -> pd.DataFrame:
        """
        Download data for a pair of stocks with aligned dates.
        
        Args:
            ticker_a: First stock symbol
            ticker_b: Second stock symbol
        
        Returns:
            DataFrame with columns [ticker_a, ticker_b]
        """
        stock_a = self.fetch_stock(ticker_a)
        stock_b = self.fetch_stock(ticker_b)
        
        if stock_a.empty or stock_b.empty:
            return pd.DataFrame()
        
        df = pd.DataFrame({
            ticker_a: stock_a,
            ticker_b: stock_b
        })
        
        df = df.dropna()
        
        if len(df) < 100:
            return pd.DataFrame()
        
        return df
    
    def fetch_multiple_stocks(self, tickers: List[str]) -> pd.DataFrame:
        """
        Download multiple stocks at once.
        
        Args:
            tickers: List of stock symbols
        
        Returns:
            DataFrame with one column per ticker
        """
        try:
            data = yf.download(tickers, start=self.start_date, end=self.end_date,
                             auto_adjust=True, progress=False)['Close']
            
            if isinstance(data, pd.Series):
                data = data.to_frame(name=tickers[0])
            
            return data.dropna()
        except Exception as e:
            print(f"Error fetching multiple stocks: {e}")
            return pd.DataFrame()


# Energy sector stock universe
ENERGY_STOCKS = {
    'brown': [
        'ATO',   
        'ETR',   
        'EQT',   
        'AEE',   
        'CTRA',   
        'CNP',   
        'CEG',   
        'TPL',   
        'NI',   
        'AEP',
        'DVN',
        'EOG',
    ],
    'green': [
        'ES',   
        'AES',  
        'EIX',  
        'SRE',  
        'PCG',   
        'OXY',   
        'KMI',   
        'AWK',  
        'OKE', 
        'MPC',
        'HAL',
        'BKR',
        
    ]
}
