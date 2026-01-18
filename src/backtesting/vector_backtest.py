import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def run_vectorized_backtest(
    ticker1: str, 
    ticker2: str, 
    entry_threshold: float = 2.0, 
    exit_threshold: float = 0.5,
    lookback_window: int = 20,
    start_date: str = "2020-01-01",
    end_date: str = "2024-05-30",
    split_date: str = "2023-01-01"
):
    """
    Runs a vectorized backtest for a pairs trading strategy.
    
    Logic aligns with src/tools/signal_tools.py:
    - Long Spread when Z < -Entry
    - Short Spread when Z > +Entry
    - Exit when |Z| < Exit
    """
    print(f"--- 📊 Running Backtest for {ticker1}/{ticker2} ---")
    
    # 1. Fetch Data
    tickers = f"{ticker1} {ticker2}"
    try:
        data = yf.download(tickers, start=start_date, end=end_date, progress=False)['Close']
    except Exception as e:
        print(f"Error downloading data: {e}")
        return None
    
    if ticker1 not in data.columns or ticker2 not in data.columns:
        print("Error: Tickers not found in data.")
        return None

    df = pd.DataFrame()
    df['Leg1'] = data[ticker1]
    df['Leg2'] = data[ticker2]
    
    # 2. Calculate Rolling Beta (Dynamic Hedge Ratio)
    window_beta = 60
    rolling_cov = df['Leg1'].rolling(window=window_beta).cov(df['Leg2'])
    rolling_var = df['Leg2'].rolling(window=window_beta).var()
    df['Hedge_Ratio_Rolling'] = rolling_cov / rolling_var
    df['Hedge_Ratio_Rolling'] = df['Hedge_Ratio_Rolling'].fillna(1.0) # Fallback

    # Calculate Spread using YESTERDAY'S Beta (Shift 1) to avoid lookahead bias
    df['Spread'] = df['Leg1'] - (df['Hedge_Ratio_Rolling'].shift(1) * df['Leg2'])
    
    # Calculate Z-Score
    df['Spread_Mean'] = df['Spread'].rolling(window=lookback_window).mean()
    df['Spread_Std'] = df['Spread'].rolling(window=lookback_window).std()
    df['Z_Score'] = (df['Spread'] - df['Spread_Mean']) / df['Spread_Std']
    
    # 3. Generate Signals 
    df['Signal'] = 0 
    
    position = 0
    signals = []
    
    for z in df['Z_Score']:
        if pd.isna(z):
            signals.append(0)
            continue
            
        if position == 0:
            if z > entry_threshold:
                position = -1 
            elif z < -entry_threshold:
                position = 1 
        else:
            if abs(z) < exit_threshold:
                position = 0
                
        signals.append(position)
        
    df['Position'] = signals
    
    df['Position_Lagged'] = df['Position'].shift(1)
    
    # 4. Calculate Returns
    df['Spread_Change'] = df['Spread'].diff()
    df['Strategy_PnL_Daily'] = df['Position_Lagged'] * df['Spread_Change']
    
    # 5. Apply Slippage / Transaction Costs
    cost_per_trade = 0.05 
    df['Trades'] = df['Position'].diff().abs().fillna(0)
    df['Transaction_Costs'] = df['Trades'] * cost_per_trade
    
    df['Net_PnL'] = df['Strategy_PnL_Daily'] - df['Transaction_Costs']

    # --- 6. PERFORMANCE METRICS & BENCHMARK COMPARISON --- 
    
    # Baseline Parameters
    rf_annual = 0.015  
    
    # A. Calculate Strategy Returns 
    capital = 100000 
    # Determine trade size (20% of capital)
    avg_price = (df['Leg1'] + df['Leg2']).mean()
    units = (capital * 0.20) / avg_price
    
    df['Strategy_Daily_Ret'] = (df['Net_PnL'] * units) / capital
    df['Strategy_Cumulative_Ret'] = (1 + df['Strategy_Daily_Ret']).cumprod() * 100 
    
    # B. Calculate Benchmark (50/50 Buy & Hold)
    df['Ret_L1'] = df['Leg1'].pct_change().fillna(0)
    df['Ret_L2'] = df['Leg2'].pct_change().fillna(0)
    df['Benchmark_Daily_Ret'] = (0.5 * df['Ret_L1']) + (0.5 * df['Ret_L2'])
    df['Benchmark_Cumulative_Ret'] = (1 + df['Benchmark_Daily_Ret']).cumprod() * 100 
    
    oos_df = df[df.index >= split_date].copy()
    
    # C. Metric Calculation Function
    def calculate_metrics(returns, cumulative_equity):
        if returns.empty: return 0, 0, 0, 0, 0
        
        # Annualized Return
        ann_ret = returns.mean() * 252 
        
        # Volatility
        ann_vol = returns.std() * np.sqrt(252) 
        
        # Sharpe Ratio
        sharpe = (ann_ret - rf_annual) / ann_vol if ann_vol != 0 else 0 
        
        # Maximum Drawdown (MDD)
        running_max = cumulative_equity.cummax()
        drawdown = (cumulative_equity - running_max) / running_max
        mdd = drawdown.min()
        
        # Profit Factor
        pos_ret = returns[returns > 0].sum()
        neg_ret = abs(returns[returns < 0].sum())
        profit_factor = pos_ret / neg_ret if neg_ret != 0 else np.inf
        
        return ann_ret, ann_vol, sharpe, mdd, profit_factor

    # Calculate Metrics for OOS
    strat_metrics = calculate_metrics(oos_df['Strategy_Daily_Ret'], oos_df['Strategy_Cumulative_Ret'])
    bench_metrics = calculate_metrics(oos_df['Benchmark_Daily_Ret'], oos_df['Benchmark_Cumulative_Ret'])
    

    print("\n" + "="*60)
    print(f"📈 PERFORMANCE REPORT (Out-of-Sample: {split_date} to {end_date})") 
    print(f"   Pair: {ticker1} / {ticker2}")
    print("="*60)
    
    metrics_df = pd.DataFrame({
        'Metric': ['Ann. Return', 'Ann. Volatility', 'Sharpe Ratio', 'Max Drawdown', 'Profit Factor'],
        'Strategy': [f"{strat_metrics[0]:.2%}", f"{strat_metrics[1]:.2%}", f"{strat_metrics[2]:.2f}", f"{strat_metrics[3]:.2%}", f"{strat_metrics[4]:.2f}"],
        'Benchmark': [f"{bench_metrics[0]:.2%}", f"{bench_metrics[1]:.2%}", f"{bench_metrics[2]:.2f}", f"{bench_metrics[3]:.2%}", f"{bench_metrics[4]:.2f}"]
    })
    print(metrics_df.to_string(index=False))
    print("="*60)
    
    # Plotting Equity Curves 
    plt.figure(figsize=(12, 6))
    plt.plot(oos_df.index, oos_df['Strategy_Cumulative_Ret'], label='Pairs Trading Strategy', color='green', lw=2)
    plt.plot(oos_df.index, oos_df['Benchmark_Cumulative_Ret'], label='Long-Only Benchmark', color='blue', alpha=0.6, linestyle='--')
    plt.axhline(100, color='black', linestyle=':', alpha=0.3)
    
    plt.title(f"Equity Curve: {ticker1}/{ticker2} (OOS Period)") 
    plt.ylabel("Portfolio Value (Base 100)")
    plt.xlabel("Date")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    if not os.path.exists("results"):
        os.makedirs("results")
    plt.savefig("results/equity_curve_oos.png")
    print("\n✅ Plot saved to results/equity_curve_oos.png")
    plt.show()

    return df

if __name__ == "__main__":
    run_vectorized_backtest("ETR", "AEP", entry_threshold=2.0)