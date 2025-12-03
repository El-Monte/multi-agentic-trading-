import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# 1. VECTOR BACKTEST FUNCTION

def run_vectorized_backtest(
    ticker1: str,
    ticker2: str,
    hedge_ratio: float| None = None,
    entry_threshold: float = 2.5,
    exit_threshold: float = 0.5,
    window: int = 20,
    start_date: str = "2020-01-01",
    end_date: str = "2024-12-30"
):
    """
    Vectorized backtest for a pairs trading strategy.
    Returns:
        - df: full dataframe
        - stats: dict with pnl, sharpe, num_trades, thresholds
    """

    print(f"\n--- Running Backtest for {ticker1}/{ticker2} ---")
    if hedge_ratio is None:
        from src.data.fetch_data import DataFetcher
        from src.analysis.cointegration import CointegrationAnalyzer

        print("Estimating hedge ratio dynamically via OLS...")

        fetcher = DataFetcher()
        pair_data = fetcher.fetch_pair(ticker1, ticker2)

        if pair_data.empty:
            print(f"[ERROR] No data available to estimate hedge ratio for {ticker1}/{ticker2}")
            return None, None

        analyzer = CointegrationAnalyzer()
        hedge_ratio = analyzer.calculate_hedge_ratio(
            pair_data[ticker1],
            pair_data[ticker2]
        )

        print(f" → Estimated hedge ratio: {hedge_ratio:.4f}")

    # 1. Fetch Data
    tickers = f"{ticker1} {ticker2}"
    data = yf.download(
        tickers, start=start_date, end=end_date,
        progress=False, auto_adjust=True
    )['Close']

    if data.empty:
        print(f"[ERROR] No data for {ticker1}/{ticker2}")
        return None, None

    df = pd.DataFrame()
    df['Leg1'] = data[ticker1]
    df['Leg2'] = data[ticker2]

    # 2. Spread & Z-score
    df['Spread'] = df['Leg1'] - (hedge_ratio * df['Leg2'])
    df['Spread_Mean'] = df['Spread'].rolling(window=window).mean()
    df['Spread_Std'] = df['Spread'].rolling(window=window).std()
    df['Z_Score'] = (df['Spread'] - df['Spread_Mean']) / df['Spread_Std']

    # 3. State Machine (vectorized logic)
    df['Position'] = 0
    position = 0
    signals = []

    for z in df['Z_Score']:
        if pd.isna(z):
            signals.append(0)
            continue
        
        if position == 0:
            if z > entry_threshold:
                position = -1   # SHORT SPREAD
            elif z < -entry_threshold:
                position = 1    # LONG SPREAD
        else:
            if abs(z) < exit_threshold:
                position = 0    # EXIT
        
        signals.append(position)

    df['Position'] = signals
    df['Position_Lagged'] = df['Position'].shift(1)

    # Trade Counting (entries only)
    df['Entry_Flag'] = ((df['Position_Lagged'] == 0) & (df['Position'] != 0)).astype(int)
    num_trades = int(df['Entry_Flag'].sum())

    # 4. PnL Computation
    df['Spread_Change'] = df['Spread'].diff()
    df['Strategy_PnL_Daily'] = df['Position_Lagged'] * df['Spread_Change']

    # Transaction costs: 5 cents per trade
    cost_per_trade = 0.05
    df['Trades'] = df['Position'].diff().abs()
    df['Transaction_Costs'] = df['Trades'] * cost_per_trade

    df['Net_PnL'] = df['Strategy_PnL_Daily'] - df['Transaction_Costs']
    df['Equity_Curve'] = df['Net_PnL'].cumsum()

    # Final Metrics
    total_pnl = float(df['Net_PnL'].sum())

    if df['Net_PnL'].std() == 0 or np.isnan(df['Net_PnL'].std()):
        sharpe_ratio = 0.0
    else:
        sharpe_ratio = float((df['Net_PnL'].mean() / df['Net_PnL'].std()) * np.sqrt(252))

    print(f"Total PnL: {total_pnl:.2f}")
    print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"Number of Trades: {num_trades}")

    stats = {
        "ticker1": ticker1,
        "ticker2": ticker2,
        "entry_threshold": entry_threshold,
        "exit_threshold": exit_threshold,
        "window": window,
        "total_pnl": total_pnl,
        "sharpe": sharpe_ratio,
        "num_trades": num_trades
    }

    return df, stats



# 2. GRID SEARCH OPTIMIZATION


def grid_search_parameters(
    ticker1: str,
    ticker2: str,
    hedge_ratio: float,
    entry_values=(1.5, 2.0, 2.5),
    exit_values=(0.2, 0.5, 0.8),
    window_values=(15, 20, 30),
    min_trades: int = 5
):
    """
    Searches for the best parameters ensuring:
      - enough trades (min_trades)
      - highest Sharpe ratio
    """

    best_sharpe = -999
    best_stats = None

    print("\n=== STARTING GRID SEARCH ===")

    for entry in entry_values:
        for exit_ in exit_values:
            for win in window_values:

                print(f"\n>>> Testing entry={entry}, exit={exit_}, window={win}")

                df, stats = run_vectorized_backtest(
                    ticker1=ticker1,
                    ticker2=ticker2,
                    hedge_ratio=hedge_ratio,
                    entry_threshold=entry,
                    exit_threshold=exit_,
                    window=win
                )

                if stats is None:
                    continue

                trades = stats["num_trades"]

                # SKIP if too few trades
                if trades < min_trades:
                    print(f" Skipped: Only {trades} trades (min={min_trades})")
                    continue

                sharpe = stats["sharpe"]

                print(f"✓ Sharpe={sharpe:.2f}, Trades={trades}")

                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_stats = stats

    print("\n=== GRID SEARCH RESULTS ===")

    if best_stats is None:
        print(" No parameter set matched min_trades constraint.")
    else:
        print(f" BEST SHARPE: {best_stats['sharpe']:.2f}")
        print(f"Parameters:")
        print(f"  Entry Threshold: {best_stats['entry_threshold']}")
        print(f"  Exit Threshold: {best_stats['exit_threshold']}")
        print(f"  Window: {best_stats['window']}")
        print(f"  Trades: {best_stats['num_trades']}")

    return best_stats



# 3. TEST BLOCK 
if __name__ == "__main__":
    
    tickerA = "NEE"
    tickerB = "CWEN"
    beta = 0.948

    print("\n🔍 Running Full Optimization...\n")

    best = grid_search_parameters(
        ticker1=tickerA,
        ticker2=tickerB,
        hedge_ratio=beta,
        entry_values=(1.5, 2.0, 2.5),
        exit_values=(0.2, 0.5, 0.8),
        window_values=(15, 20, 30),
        min_trades=5
    )

    print("\nFinal Best Params:")
    print(best)
