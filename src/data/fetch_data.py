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
    
    def __init__(self, start_date: str = "2015-01-01", end_date: str = "2025-01-01"):
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
            
            # Return Close price as Series with proper index
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
        
        # Check if we got valid data
        if stock_a.empty or stock_b.empty:
            return pd.DataFrame()
        
        # Combine and drop NaN (align trading days)
        df = pd.DataFrame({
            ticker_a: stock_a,
            ticker_b: stock_b
        })
        
        # Drop rows with any NaN values
        df = df.dropna()
        
        # Ensure we have enough data
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
            
            # Handle single ticker case
            if isinstance(data, pd.Series):
                data = data.to_frame(name=tickers[0])
            
            return data.dropna()
        except Exception as e:
            print(f"Error fetching multiple stocks: {e}")
            return pd.DataFrame()


# Energy sector stock universe
ENERGY_STOCKS = {
    'brown': [
        'XOM',   # ExxonMobil - Integrated Oil
        'CVX',   # Chevron - Integrated Oil
        'COP',   # ConocoPhillips - E&P
        'SLB',   # Schlumberger - Services
        'EOG',   # EOG Resources - E&P
        'PSX',   # Phillips 66 - Refining
        'VLO',   # Valero - Refining
        'MPC',   # Marathon Petroleum - Refining
        'OXY',   # Occidental - E&P
        'HAL',   # Halliburton - Services
        'KMI',   # Kinder Morgan - Midstream
        'WMB',   # Williams Companies - Midstream
        'OKE',   # ONEOK - Midstream
        'BP',    # BP - Integrated Oil
        'SHEL'   # Shell - Integrated Oil
    ],
    'green': [
        'NEE',   # NextEra Energy - Utility + Renewables
        'FSLR',  # First Solar - Solar Manufacturing
        'ENPH',  # Enphase - Solar Inverters
        'SEDG',  # SolarEdge - Solar Inverters
        'RUN',   # Sunrun - Residential Solar
        'AES',   # AES Corporation - Renewable Utility
        'BEP',   # Brookfield Renewable - Pure-play Renewables
        'CWEN',  # Clearway Energy - Renewables
        'PLUG',  # Plug Power - Hydrogen
        'BE',    # Bloom Energy - Fuel Cells
        'ICLN',  # iShares Clean Energy ETF
        'TAN',   # Invesco Solar ETF
        'QCLN',  # First Trust Clean Edge ETF
        'PBW',   # Invesco WilderHill Clean Energy
        'ACES'   # ALPS Clean Energy ETF
    ]
}