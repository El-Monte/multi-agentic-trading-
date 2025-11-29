import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def run_vectorized_backtest(
    ticker1: str, 
    ticker2: str, 
    hedge_ratio: float, 
    entry_threshold: float = 2.5, 
    exit_threshold: float = 0.5,
    start_date: str = "2020-01-01",
    end_date: str = "2024-12-30"
):
    """
    Runs a vectorized backtest for a pairs trading strategy.
    
    Logic aligns with src/tools/signal_tools.py:
    - Long Spread when Z < -Entry
    - Short Spread when Z > +Entry
    - Exit when |Z| < Exit
    """
    print(f"--- Running Backtest for {ticker1}/{ticker2} ---")
    
    # 1. Fetch Data
    tickers = f"{ticker1} {ticker2}"
    data = yf.download(tickers, start=start_date, end=end_date, progress=False, auto_adjust=True)['Close']
    
    # Rename columns for clarity
    df = pd.DataFrame()
    df['Leg1'] = data[ticker1]
    df['Leg2'] = data[ticker2]
    
    # 2. Calculate Spread and Z-Score
    # Spread = Leg1 - (Hedge_Ratio * Leg2)
    df['Spread'] = df['Leg1'] - (hedge_ratio * df['Leg2'])
    
    # Rolling Window (20 days) matches our Tool
    window = 20
    df['Spread_Mean'] = df['Spread'].rolling(window=window).mean()
    df['Spread_Std'] = df['Spread'].rolling(window=window).std()
    df['Z_Score'] = (df['Spread'] - df['Spread_Mean']) / df['Spread_Std']
    
    # 3. Generate Signals (Vectorized Logic)
    # We use a trick with 'Shift' to avoid look-ahead bias
    df['Signal'] = 0 # 0 = Flat, 1 = Long Spread, -1 = Short Spread
    
    # Create a state machine using iteration (Vectorizing signal state is hard in pure pandas)
    position = 0
    signals = []
    
    for z in df['Z_Score']:
        if pd.isna(z):
            signals.append(0)
            continue
            
        if position == 0:
            # Entry Logic
            if z > entry_threshold:
                position = -1 # Short Spread
            elif z < -entry_threshold:
                position = 1  # Long Spread
        else:
            # Exit Logic
            if abs(z) < exit_threshold:
                position = 0
                
        signals.append(position)
        
    df['Position'] = signals
    
    # Shift position by 1 day! 
    # Why? We calculate signal at Close of Day T, so we trade at Open of Day T+1 (or Close T+1)
    # This prevents "Looking into the future"
    df['Position_Lagged'] = df['Position'].shift(1)
    
    # 4. Calculate Returns
    # Spread Return = Change in Spread * Position
    df['Spread_Change'] = df['Spread'].diff()
    df['Strategy_PnL_Daily'] = df['Position_Lagged'] * df['Spread_Change']
    
    # 5. Apply Slippage / Transaction Costs
    # Every time the position changes, we pay costs
    # Cost = 10 bps (0.1%) of the Asset Price roughly. 
    # For a spread trade, let's estimate $0.05 per share traded as friction.
    cost_per_trade = 0.05 
    df['Trades'] = df['Position'].diff().abs() # 1 if we opened/closed, 2 if we flipped
    df['Transaction_Costs'] = df['Trades'] * cost_per_trade
    
    df['Net_PnL'] = df['Strategy_PnL_Daily'] - df['Transaction_Costs']
    
    # 6. Cumulative Returns (Equity Curve)
    df['Equity_Curve'] = df['Net_PnL'].cumsum()
    
    # 7. Print Stats
    total_return = df['Net_PnL'].sum()
    sharpe_ratio = (df['Net_PnL'].mean() / df['Net_PnL'].std()) * np.sqrt(252) # Annualized
    
    print(f"Total PnL (Points): {total_return:.2f}")
    print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
    
    return df

# Main Execution Block
if __name__ == "__main__":
    # Pair 3: PLUG vs RUN
    ticker_a = "PLUG"
    ticker_b = "RUN"
    beta = 0.872
    
    results = run_vectorized_backtest(ticker_a, ticker_b, beta)
    
    results = run_vectorized_backtest(ticker_a, ticker_b, beta)
    
    # Plotting
    plt.figure(figsize=(12, 6))
    
    # Subplot 1: Equity Curve
    plt.subplot(2, 1, 1)
    plt.plot(results.index, results['Equity_Curve'], label='Strategy Equity', color='green')
    plt.title(f"Backtest Results: {ticker_a}/{ticker_b} (Net PnL)")
    plt.grid(True)
    
    # Subplot 2: Z-Score and Thresholds
    plt.subplot(2, 1, 2)
    plt.plot(results.index, results['Z_Score'], label='Z-Score', alpha=0.6)
    plt.axhline(2.5, color='red', linestyle='--', label='Short Thresh')
    plt.axhline(-2.5, color='green', linestyle='--', label='Long Thresh')
    plt.axhline(0, color='black', alpha=0.3)
    plt.fill_between(results.index, 2.5, -2.5, color='gray', alpha=0.1)
    plt.title("Z-Score Signal Generation")
    plt.legend()
    
    plt.tight_layout()
    plt.show() # This will open a window with the graph