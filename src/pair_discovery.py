#!/usr/bin/env python3
"""
Day 1: Automated Pair Discovery Script
=======================================

Screens energy sector stocks for cointegrated pairs and selects
the top 3 candidates for our multi-agent trading system.

Usage:
    python scripts/run_pair_discovery.py

Output Files:
    - data/processed/all_pairs_results.csv       (Full screening data)
    - data/processed/qualified_pairs.csv         (Only pairs that pass criteria)
    - data/processed/top_3_pairs.txt             (Human-readable top 3)
    - data/processed/selected_pairs_config.yaml  (Config for next steps)
    - reports/figures/*.png                      (Visualizations)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data.fetch_data import DataFetcher, ENERGY_STOCKS
from src.analysis.cointegration import CointegrationAnalyzer, screen_all_pairs
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import yaml
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 11


def setup_directories():
    """Create necessary directories if they don't exist."""
    dirs = [
        'data/raw',
        'data/processed',
        'reports/figures',
        'scripts'
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def print_header(text, char="="):
    """Print a formatted header."""
    width = 70
    print("\n" + char * width)
    print(text.center(width))
    print(char * width + "\n")


def print_progress(current, total, prefix="Progress"):
    """Print progress bar."""
    bar_length = 40
    filled = int(bar_length * current / total)
    bar = "█" * filled + "░" * (bar_length - filled)
    percent = 100 * current / total
    print(f"\r{prefix}: |{bar}| {percent:.1f}% ({current}/{total})", end="")
    if current == total:
        print()


def screen_pairs(fetcher, analyzer):
    """Screen all brown/brown and green/green pairs."""
    print_header("🔍 SCREENING BROWN/BROWN PAIRS")
    
    brown_results = screen_all_pairs(
        ENERGY_STOCKS['brown'],
        ENERGY_STOCKS['brown'],
        fetcher,
        analyzer
    )
    
    print(f" Analyzed {len(brown_results)} brown pairs")
    
    if len(brown_results) > 0:
        print("\n🏆 Top 3 Brown Pairs:")
        top_3 = brown_results.head(3)
        for i, row in top_3.iterrows():
            print(f"   {i+1}. {row['pair']:<15} | Score: {row['score']:.1f} | "
                  f"Corr: {row['correlation']:.3f} | Half-life: {row['half_life']:.1f}d")
    
    print_header("🔍 SCREENING GREEN/GREEN PAIRS")
    
    green_results = screen_all_pairs(
        ENERGY_STOCKS['green'],
        ENERGY_STOCKS['green'],
        fetcher,
        analyzer
    )
    
    print(f" Analyzed {len(green_results)} green pairs")
    
    if len(green_results) > 0:
        print("\n🏆 Top 3 Green Pairs:")
        top_3 = green_results.head(3)
        for i, row in top_3.iterrows():
            print(f"   {i+1}. {row['pair']:<15} | Score: {row['score']:.1f} | "
                  f"Corr: {row['correlation']:.3f} | Half-life: {row['half_life']:.1f}d")
    
    return brown_results, green_results


def filter_qualified_pairs(brown_results, green_results):
    """Apply qualification criteria."""
    print_header("🎯 FILTERING QUALIFIED PAIRS")
    
    def is_qualified(row):
        return (
            row['eg_pvalue'] < 0.15 and       
            row['correlation'] > 0.60 and     
            row['half_life'] < 150 and       
            row['half_life'] > 5 and        
            row['hurst'] < 0.70            
        )
    
    brown_qualified = brown_results[brown_results.apply(is_qualified, axis=1)] if len(brown_results) > 0 else pd.DataFrame()
    green_qualified = green_results[green_results.apply(is_qualified, axis=1)] if len(green_results) > 0 else pd.DataFrame()
    
    print(f"\n Qualification Criteria (RELAXED FOR ENERGY SECTOR):")
    print(f"   ✓ Engle-Granger p-value < 0.15")
    print(f"   ✓ Correlation > 0.60")
    print(f"   ✓ Half-life: 5-150 days")
    print(f"   ✓ Hurst exponent < 0.70")
    
    print(f"\n Results:")
    print(f"   Brown pairs qualified: {len(brown_qualified)}/{len(brown_results)}")
    print(f"   Green pairs qualified: {len(green_qualified)}/{len(green_results)}")
    
    return brown_qualified, green_qualified


def plot_pair(ticker_a, ticker_b, fetcher, analyzer, output_path):
    """Create visualization for a pair."""
    try:
        data = fetcher.fetch_pair(ticker_a, ticker_b)
        
        if len(data) < 100:
            return False
        
        hedge_ratio = analyzer.calculate_hedge_ratio(data[ticker_a], data[ticker_b])
        spread = analyzer.calculate_spread(data[ticker_a], data[ticker_b], hedge_ratio)
        
        fig, axes = plt.subplots(2, 1, figsize=(14, 8))
        
        # Plot 1: Normalized prices
        ax1 = axes[0]
        norm_a = data[ticker_a] / data[ticker_a].iloc[0]
        norm_b = data[ticker_b] / data[ticker_b].iloc[0]
        norm_a.plot(ax=ax1, label=ticker_a, linewidth=2, color='#2E86AB')
        norm_b.plot(ax=ax1, label=ticker_b, linewidth=2, color='#A23B72')
        ax1.set_title(f"{ticker_a}/{ticker_b} - Normalized Price Comparison", 
                     fontsize=14, fontweight='bold', pad=15)
        ax1.set_ylabel("Normalized Price (Base = 1.0)", fontsize=12)
        ax1.legend(fontsize=11, loc='best')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Spread Z-score
        ax2 = axes[1]
        spread_z = (spread - spread.mean()) / spread.std()
        spread_z.plot(ax=ax2, linewidth=1.5, color='black', label='Spread Z-Score')
        ax2.axhline(2.0, color='red', linestyle='--', label='±2σ Entry', linewidth=1.5, alpha=0.7)
        ax2.axhline(-2.0, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
        ax2.axhline(0, color='blue', linestyle='-', alpha=0.5, linewidth=1)
        ax2.fill_between(spread_z.index, 2.0, spread_z.max(), alpha=0.1, color='red')
        ax2.fill_between(spread_z.index, -2.0, spread_z.min(), alpha=0.1, color='red')
        ax2.set_title("Spread Z-Score (Trading Signal)", fontsize=12, pad=10)
        ax2.set_ylabel("Standard Deviations from Mean", fontsize=11)
        ax2.set_xlabel("Date", fontsize=11)
        ax2.legend(fontsize=10, loc='best')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return True
        
    except Exception as e:
        print(f"   ⚠️  Could not plot {ticker_a}/{ticker_b}: {str(e)[:50]}")
        return False


def save_results(all_qualified, top_3, brown_results, green_results, fetcher, analyzer):
    """Save all results in multiple formats."""
    print_header("💾 SAVING RESULTS")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Save all screening results (CSV)
    all_results = pd.concat([brown_results, green_results]).sort_values('score', ascending=False)
    csv_path = 'data/processed/all_pairs_results.csv'
    all_results.to_csv(csv_path, index=False)
    print(f"✅ Saved: {csv_path} ({len(all_results)} pairs)")
    
    # 2. Save qualified pairs only (CSV)
    if len(all_qualified) > 0:
        qualified_path = 'data/processed/qualified_pairs.csv'
        all_qualified.to_csv(qualified_path, index=False)
        print(f"✅ Saved: {qualified_path} ({len(all_qualified)} pairs)")
    
    # 3. Save top 3 as human-readable text
    txt_path = 'data/processed/top_3_pairs.txt'
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write("MULTI-AGENT PAIRS TRADING - TOP 3 SELECTED PAIRS\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*70 + "\n\n")
        
        if len(top_3) == 0:
            f.write(" NO QUALIFIED PAIRS FOUND\n\n")
            f.write("Consider relaxing criteria:\n")
            f.write("- Correlation > 0.60 (instead of 0.65)\n")
            f.write("- Half-life < 75 days (instead of 60)\n")
            f.write("- Hurst < 0.60 (instead of 0.55)\n")
        else:
            for i, row in top_3.iterrows():
                rank = i + 1
                f.write(f"RANK {rank}: {row['pair']}\n")
                f.write("-" * 70 + "\n")
                f.write(f"Overall Score:        {row['score']:.1f}/100\n\n")
                
                f.write(f" Statistical Measures:\n")
                f.write(f"   Correlation:       {row['correlation']:.4f}\n")
                f.write(f"   Hedge Ratio:       {row['hedge_ratio']:.4f}\n\n")
                
                f.write(f"Cointegration Test:\n")
                f.write(f"   EG p-value:        {row['eg_pvalue']:.6f} {'✓ PASS' if row['eg_pvalue'] < 0.05 else '✗ FAIL'}\n")
                f.write(f"   Cointegrated:      {'Yes' if row['cointegrated'] else 'No'}\n\n")
                
                f.write(f" Mean Reversion:\n")
                f.write(f"   Half-life:         {row['half_life']:.2f} days\n")
                f.write(f"   Hurst Exponent:    {row['hurst']:.4f} {'(mean-reverting)' if row['hurst'] < 0.5 else '(trending)'}\n\n")
                
                f.write(f"Spread Statistics:\n")
                f.write(f"   ADF p-value:       {row['adf_pvalue']:.6f} {'✓ Stationary' if row['adf_pvalue'] < 0.05 else '✗ Non-stationary'}\n")
                f.write(f"   Spread Mean:       {row['spread_mean']:.4f}\n")
                f.write(f"   Spread Std Dev:    {row['spread_std']:.4f}\n")
                
                f.write("\n" + "="*70 + "\n\n")
            
            f.write("\n TRADING LOGIC:\n")
            f.write("-" * 70 + "\n")
            f.write("When Z-score > 2.5:  Short the spread (short stock A, long stock B)\n")
            f.write("When Z-score < -2.5: Long the spread (long stock A, short stock B)\n")
            f.write("When Z-score → 0:    Exit position (mean reversion complete)\n\n")
            
            f.write("💡 INTERPRETATION:\n")
            f.write("-" * 70 + "\n")
            f.write("- Lower half-life = faster mean reversion = more frequent trades\n")
            f.write("- Hurst < 0.5 = mean-reverting behavior (good for pairs trading)\n")
            f.write("- High correlation = stocks move together (reduces basis risk)\n")
            f.write("- Low EG p-value = strong cointegration (stable long-term relationship)\n")
    
    print(f" Saved: {txt_path}")
    
    if len(top_3) > 0:
        yaml_path = 'data/processed/selected_pairs_config.yaml'
        config = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_pairs_screened': len(all_results),
                'qualified_pairs': len(all_qualified),
                'selected_pairs': len(top_3)
            },
            'pairs': []
        }
        
        for i, row in top_3.iterrows():
            ticker_a, ticker_b = row['pair'].split('/')
            config['pairs'].append({
                'rank': i + 1,
                'ticker_a': ticker_a,
                'ticker_b': ticker_b,
                'hedge_ratio': float(row['hedge_ratio']),
                'correlation': float(row['correlation']),
                'half_life_days': float(row['half_life']),
                'hurst_exponent': float(row['hurst']),
                'score': float(row['score'])
            })
        
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        print(f" Saved: {yaml_path}")
    
    print(f"\n Generating visualizations...")
    viz_count = 0
    for i, row in top_3.iterrows():
        ticker_a, ticker_b = row['pair'].split('/')
        output_path = f'reports/figures/pair_{i+1}_{ticker_a}_{ticker_b}.png'
        if plot_pair(ticker_a, ticker_b, fetcher, analyzer, output_path):
            print(f"   Created: {output_path}")
            viz_count += 1
    
    print(f"\n Generated {viz_count} visualization(s)")


def print_summary(brown_results, green_results, all_qualified, top_3):
    """Print final summary."""
    print_header("📊 SUMMARY REPORT")
    
    total_tested = len(brown_results) + len(green_results)
    total_qualified = len(all_qualified)
    
    summary = f"""
   Screening Results:
   Total pairs tested:     {total_tested}
   Qualified pairs:        {total_qualified}
   Success rate:           {100*total_qualified/max(total_tested, 1):.1f}%
   
   Top 3 Selected Pairs:"""
    
    print(summary)
    
    if len(top_3) == 0:
        print("\n   NO PAIRS MET QUALIFICATION CRITERIA")
        print("\n   Suggestions:")
        print("   - Check if data downloaded correctly")
        print("   - Relax qualification thresholds")
        print("   - Expand stock universe")
    else:
        for i, row in top_3.iterrows():
            print(f"\n   {i+1}. {row['pair']}")
            print(f"      Score: {row['score']:.1f}/100")
            print(f"      Correlation: {row['correlation']:.3f}")
            print(f"      Half-life: {row['half_life']:.1f} days")
    
    print("\n" + "="*70)
    print(" DAY 1 COMPLETE!")
    print("="*70)
    print("\n Output Files:")
    print("   - data/processed/top_3_pairs.txt         (Read this first!)")
    print("   - data/processed/all_pairs_results.csv   (Full data)")
    print("   - data/processed/qualified_pairs.csv     (Filtered pairs)")
    print("   - data/processed/selected_pairs_config.yaml (For Day 2)")
    print("   - reports/figures/*.png                  (Charts)")
    


def main():
    """Main execution."""
    print_header("🤖 MULTI-AGENT PAIRS TRADING - DAY 1", "=")
    print("Pair Discovery & Statistical Validation\n")
    
    setup_directories()
    
    print(" Initializing components...")
    fetcher = DataFetcher(start_date="2015-01-01", end_date="2023-01-01")
    analyzer = CointegrationAnalyzer()
    print(f"   Stock universe: {len(ENERGY_STOCKS['brown'])} brown + {len(ENERGY_STOCKS['green'])} green")
    
    brown_results, green_results = screen_pairs(fetcher, analyzer)
    
    brown_qualified, green_qualified = filter_qualified_pairs(brown_results, green_results)
    
    # Select top 3
    print_header(" SELECTING TOP 3 PAIRS")
    all_qualified = pd.concat([brown_qualified, green_qualified]).sort_values('score', ascending=False)
    top_3 = all_qualified.head(3)
    
    if len(top_3) > 0:
        print("🏆 TOP 3 PAIRS SELECTED:\n")
        for i, row in top_3.iterrows():
            print(f"   {i+1}. {row['pair']:<12} | Score: {row['score']:>5.1f} | "
                  f"Corr: {row['correlation']:.3f} | Half-life: {row['half_life']:>5.1f}d")
    
    save_results(all_qualified, top_3, brown_results, green_results, fetcher, analyzer)
    print_summary(brown_results, green_results, all_qualified, top_3)


if __name__ == "__main__":
    main()
