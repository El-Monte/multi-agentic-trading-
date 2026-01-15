
# %%
import yfinance as yf
import pandas as pd
import numpy as np
import random
import logging
import json
import refinitiv.data as rd
from typing import List, Dict, Tuple
from datetime import datetime
import warnings


# %%
"""
ESG-based stock selection and data fetching for pairs trading.
Uses Refinitiv Data Platform API for ESG data and Yahoo Finance for price data.
Automatically selects Brown/Green stocks from S&P 500 based on Environment scores.
Uses random sampling for stock selection.

INSTALLATION:
pip install refinitiv-data yfinance pandas numpy

REQUIREMENTS:
- refinitiv-data.config file with API key credentials
- Active Refinitiv Data Platform subscription
"""

# Check if refinitiv.data is installed
try:
    import refinitiv.data as rd
    REFINITIV_AVAILABLE = True
except ImportError:
    REFINITIV_AVAILABLE = False
    print("="*60)
    print("⚠️  WARNING: refinitiv-data package not found!")
    print("="*60)
    print("\nPlease install it using:")
    print("  pip install refinitiv-data")
    print("="*60)

# Suppress warnings
warnings.filterwarnings('ignore')
logging.getLogger('yfinance').setLevel(logging.CRITICAL)

# Set random seed for reproducibility (optional - remove for true randomness)
random.seed(42)
np.random.seed(42)


class RefinitivESGSelector:
    """Select stocks based on ESG scores from S&P 500 using Refinitiv Data Platform API."""
    
    def __init__(self, config_file: str = "refinitiv-data.config"):
        """
        Initialize selector with S&P 500 tickers and Refinitiv API credentials.
        
        Args:
            config_file: Path to Refinitiv configuration file with API key
        """
        if not REFINITIV_AVAILABLE:
            raise ImportError(
                "refinitiv-data package is not installed. "
                "Please run: pip install refinitiv-data"
            )
        
        self.config_file = config_file
        self.sp500_tickers = self._get_sp500_tickers()
        self.energy_sectors = ['Energy', 'Utilities']
        self._initialize_refinitiv()
        print(f"Loaded {len(self.sp500_tickers)} S&P 500 tickers from GitHub")
        
    def _initialize_refinitiv(self):
        """Initialize Refinitiv Data Platform API connection using API key from config file."""
        try:
            # Simply use the config file - let Refinitiv library handle the parsing
            # The library will automatically read the credentials from the file
            rd.open_session(config_name=self.config_file)
            
            print("✓ Successfully connected to Refinitiv Data Platform API")
            
        except FileNotFoundError:
            print(f"❌ ERROR: Configuration file '{self.config_file}' not found!")
            print(f"\nPlease ensure the file 'refinitiv-data.config' exists in: {os.getcwd()}")
            raise
        except Exception as e:
            print(f"❌ ERROR: Failed to connect to Refinitiv: {e}")
            print("\nMake sure:")
            print("1. Your API key is valid and active")
            print("2. You have an active Refinitiv Data Platform subscription")
            print("3. Your credentials in the config file are correct")
            print("4. Your network allows API access to Refinitiv servers")
            print(f"\nConfig file location: {os.path.abspath(self.config_file)}")
            
            # Try to show what's in the config file (without exposing credentials)
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    print(f"\nConfig file structure detected:")
                    print(f"  - Has 'sessions' key: {'sessions' in config}")
                    if 'sessions' in config:
                        print(f"  - Session keys: {list(config['sessions'].keys())}")
            except:
                pass
            
            raise
        
    def _get_sp500_tickers(self) -> List[str]:
        """
        Fetch current S&P 500 constituents from GitHub dataset.
        
        Returns:
            List of ticker symbols
        """
        try:
            url = 'https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv'
            df = pd.read_csv(url)
            return df['Symbol'].tolist()
        except Exception as e:
            print(f"Error fetching S&P 500 list from GitHub: {e}")
            return []
    
    def _convert_ticker_to_ric(self, ticker: str) -> str:
        """
        Convert Yahoo ticker to Refinitiv RIC (Reuters Instrument Code).
        
        Args:
            ticker: Yahoo Finance ticker (e.g., 'AAPL')
        
        Returns:
            Refinitiv RIC (e.g., 'AAPL.O' for NASDAQ, 'AAPL.N' for NYSE)
        """
        # Handle special cases with dots
        special_cases = {
            'BRK.B': 'BRKb.N',
            'BF.B': 'BFb.N'
        }
        
        if ticker in special_cases:
            return special_cases[ticker]
        
        # Remove any existing suffixes from Yahoo (like -USD)
        base_ticker = ticker.split('.')[0].split('-')[0]
        
        # For US stocks, try multiple exchange suffixes
        # We'll return a list to try multiple options
        return base_ticker  # Return just the base ticker, let Refinitiv resolve it
    
    def _try_multiple_rics(self, ticker: str) -> List[str]:
     """
      Genera le variazioni RIC più comuni per l'accesso ai dati ESG.
      Refinitiv non è in grado di risolvere il ticker nudo per tutti i campi.
    """
     base = self._convert_ticker_to_ric(ticker)
    
    # 💥 CORREZIONE CRUCIALE: Forzare i suffissi per la risoluzione ESG 💥
    # Per i dati ESG su Refinitiv, è quasi sempre necessario il suffisso.
     return [
        f"{base}.O",     # NASDAQ (la maggior parte delle tech)
        f"{base}.N",     # NYSE (industriali, finanziari, energetici)
        f"{base}.OQ",    # NASDAQ alternative
        base             # Lasciamo il base come ultima opzione
    ]
    
    def fetch_esg_scores(self, tickers: List[str] = None) -> pd.DataFrame:
        """
        Fetch Environment scores from Refinitiv Data Platform API for given tickers.
        
        Args:
            tickers: List of ticker symbols (defaults to S&P 500)
        
        Returns:
            DataFrame with columns: [ticker, ric, sector, industry, environment_score, esg_score]
        """
        if tickers is None:
            tickers = self.sp500_tickers
        
        print(f"\nFetching Environment scores from Refinitiv API for {len(tickers)} stocks...")
        print("This may take several minutes. Testing connection and data access first...\n")
        
        esg_data = []
        success_count = 0
        fail_count = 0
        
        # STEP 1: Test API connection and data access
        print("="*60)
        print("TESTING API CONNECTION AND ESG DATA ACCESS")
        print("="*60)
        
        # Test 1: Basic fields to check access
        print("\n[Test 1] Checking basic ESG data access with AAPL...")
        test_fields = [
            'TR.TRESGRating',           # Rating letterale (più semplice)
            'TR.TRESGScore',            # Score numerico complessivo
            'TR.TRBCEconomicSector'     # Settore (non-ESG, dovrebbe funzionare)
        ]
        
        try:
            test_response = rd.get_data(
                universe=['AAPL.OQ'],
                fields=test_fields
            )
            print(f"✓ Test 1 successful!")
            if test_response is not None and not test_response.empty:
                print(f"  Data received: {test_response.shape[0]} rows, {test_response.shape[1]} columns")
                print(f"  Columns: {list(test_response.columns)}")
                print(f"  Sample data:\n{test_response.to_string()}\n")
                
                # Check what fields actually returned data
                has_esg_rating = 'ESG Rating' in test_response.columns
                has_esg_score = 'ESG Score' in test_response.columns
                has_sector = 'TRBC Economic Sector' in test_response.columns
                
                print(f"  Has ESG Rating: {has_esg_rating}")
                print(f"  Has ESG Score: {has_esg_score}")
                print(f"  Has Sector: {has_sector}")
                
                if not has_esg_rating and not has_esg_score:
                    print("\n  ⚠️  WARNING: No ESG data returned!")
                    print("  Your API key may not have ESG data entitlements.")
            else:
                print("  ✗ No data returned")
                
        except Exception as e:
            print(f"✗ Test 1 failed: {e}")
            print("\n⚠️  Cannot proceed - API connection or permissions issue")
            return pd.DataFrame()
        
        # Test 2: Try Environment specific fields
        print("\n[Test 2] Checking Environment Score access...")
        env_fields = [
            'TR.TRESGScore',
            'TR.CommonName'
        ]
        
        try:
            test_response2 = rd.get_data(
                universe=['AAPL'],
                fields=env_fields
            )
            print(f"✓ Test 2 successful!")
            if test_response2 is not None and not test_response2.empty:
                print(f"  Sample data:\n{test_response2.to_string()}\n")
                
               
        except Exception as e:
            print(f"✗ Test 2 failed: {e}")
        
        print("\n" + "="*60)
        print("STARTING FULL DATA COLLECTION")
        print("="*60 + "\n")
        
        # STEP 2: Use the fields that work based on tests
        # Prioritize simpler fields that are more likely to be available
        # Sostituisci l'elenco dei campi in fetch_esg_scores:
        fields = [
        'TR.TRESGScore', # ESG Combined Score (LO USEREMO PER LA CLASSIFICAZIONE)
        'TR.TRBCEconomicSector', # Settore
        'TR.TRBCIndustry', # Industria
        'TR.CommonName',
        'TR.HQCountryCode'
    # Rimuovi TR.EnvironmentPillarScore, TR.SocialPillarScore, TR.GovernancePillarScore
       ]
        # Process in smaller batches
        batch_size = 25
        
        for i in range(0, len(tickers), batch_size):
            batch_tickers = tickers[i:i+batch_size]
            
            # Try multiple RIC variations for each ticker
            batch_rics = []
            ticker_ric_map = {}
            
            for ticker in batch_tickers:
                ric_options = self._try_multiple_rics(ticker)
                primary_ric = ric_options[0]  # Use first option as primary
                batch_rics.append(primary_ric)
                ticker_ric_map[primary_ric] = ticker
            
            if (i // batch_size + 1) % 3 == 0:
                print(f"Progress: Batch {i//batch_size + 1}/{(len(tickers)-1)//batch_size + 1} | ✓ {success_count} | ✗ {fail_count}")
            
            try:
                # Request data from Refinitiv
                response = rd.get_data(
                    universe=batch_rics,
                    fields=fields
                )
                
                if response is not None and not response.empty:
                    response = response.rename(columns={
                      # Ridenominazioni confermate dall'output del Test 1:
                       'TR.TRESGScore': 'ESG Score', 
                       'TR.TRBCEconomicSector': 'TRBC Economic Sector Name', # Usa il nome completo!
                     })
                    # Process each row
                    for idx, row in response.iterrows():
                        ric = row.get('Instrument', '')
                        
                        # Get scores
                        esg_score_value = row.get('ESG Score', None)
                        env_score_proxy = esg_score_value
                        # Find corresponding ticker
                        ticker = ticker_ric_map.get(ric, ric.split('.')[0] if '.' in ric else ric)
                        
                        # Accept if we have at least Environment Score
                        if env_score_proxy is not None and not pd.isna(env_score_proxy) and float(env_score_proxy) > 0:
                            success_count += 1
                            sector_value = row.get('TRBC Economic Sector Name', 'Unknown')
                            common_name = row.get('Common Name', '') 
                            country_code = row.get('HQ Country Code', 'US')


                            esg_data.append({
                                'ticker': ticker,
                                'ric': ric,
                                'sector': sector_value,  
                                'industry': row.get('TRBC Industry', 'Unknown'),
                                'company_name': common_name,
                                'country': country_code,
                                'environment_score': float(env_score_proxy),
                                'esg_score': float(esg_score_value) if esg_score_value is not None else None,
                                
                            })

                        else:
                            fail_count += 1
                else:
                    fail_count += len(batch_rics)
                
            except Exception as e:
                print(f"  Warning: Batch {i//batch_size + 1} error: {str(e)[:100]}")
                fail_count += len(batch_rics)
        
        result_df = pd.DataFrame(esg_data)
        
        # Try to enrich with sector data from Yahoo Finance if we have results
        if not result_df.empty:
            print("\nEnriching data with sector information from Yahoo Finance...")
            for idx, row in result_df.iterrows():
                try:
                    stock = yf.Ticker(row['ticker'])
                    info = stock.info
                    result_df.at[idx, 'sector'] = info.get('sector', 'Unknown')
                    result_df.at[idx, 'industry'] = info.get('industry', 'Unknown')
                except:
                    pass
        
        print(f"\n{'='*60}")
        print(f"FETCHING COMPLETE")
        print(f"{'='*60}")
        print(f"Total stocks processed: {len(tickers)}")
        print(f"✓ Stocks with Environment Score: {success_count}")
        print(f"✗ Stocks without ESG data: {fail_count}")
        print(f"Success rate: {(success_count/len(tickers)*100):.1f}%")
        
        if len(result_df) == 0:
            print("\n⚠️  WARNING: No Environment scores found!")
            print("\nBased on the tests above:")
            print("- If Test 1 failed: API connection or permissions issue")
            print("- If Test 1 passed but Test 2 failed: No ESG data entitlements")
            print("- If both tests passed: RIC conversion or coverage issues")
            print("\nRECOMMENDATION: Contact Refinitiv support to verify ESG data access")
        elif success_count < 30:
            print(f"\n⚠️  WARNING: Only {success_count} stocks with ESG data.")
            print("This may indicate limited ESG coverage or RIC conversion issues.")
        
        return result_df
    
    def select_brown_green_stocks(self, 
                             esg_df: pd.DataFrame,
                             n_brown: int = 12,
                             n_green: int = 12,
                             energy_focus: bool = True,
                             brown_percentile: float = 0.25,
                             green_percentile: float = 0.75,
                             random_seed: int = None) -> Dict[str, List[str]]:
        if random_seed is not None:
         random.seed(random_seed)
         np.random.seed(random_seed)

    # 1. PREPARAZIONE DEL POOL COMPLETO E CALCOLO DELLE SOGLIE
        eligible_df = esg_df.copy()
    
    # Ordina il pool completo per calcolare i quantili (necessari per i threshold)
        sorted_full_df = eligible_df.sort_values('environment_score')

    # Calcola le soglie del percentile sul DataFrame completo (non filtrato per settore)
        brown_threshold = sorted_full_df['environment_score'].quantile(brown_percentile)
        green_threshold = sorted_full_df['environment_score'].quantile(green_percentile)
        # Aggiungi una colonna per la classificazione preliminare (su tutti i dati)
        eligible_df['esg_quantile'] = pd.qcut(
           eligible_df['environment_score'], 
           [0, brown_percentile, green_percentile, 1], 
           labels=['Brown', 'Mid', 'Green'],
           duplicates='drop'
        )
        eligible_df = eligible_df[eligible_df['esg_quantile'] != 'Mid'] # Togli i "neutrali"
        best_sector = None
    # Raggruppa per settore per trovare quello con più candidati Green e Brown
        for sector_name, group in eligible_df.groupby('sector'):
          brown_count = len(group[group['esg_quantile'] == 'Brown'])
          green_count = len(group[group['esg_quantile'] == 'Green'])
        
          min_count = min(brown_count, green_count)
        
          if min_count >= n_brown and min_count >= n_green:
            best_sector = sector_name
            break
        if best_sector is None:
          print("\n⚠️ Attenzione: Nessun singolo settore bilanciato trovato. Uso il settore con più titoli Green/Brown.")
        
          sector_summary = eligible_df.groupby('sector')['esg_quantile'].value_counts().unstack(fill_value=0)
          sector_summary['Min_Count'] = sector_summary[['Brown', 'Green']].min(axis=1)
        
          best_sector = sector_summary['Min_Count'].idxmax()
        # Filtra l'intero pool in base al settore selezionato
        sector_df = eligible_df[eligible_df['sector'] == best_sector].copy()

    # Definisci i pool finali per la selezione
        brown_pool = sector_df[sector_df['esg_quantile'] == 'Brown']
        green_pool = sector_df[sector_df['esg_quantile'] == 'Green']
        
        print(f"\n✅ Settore selezionato per il pair trading: {best_sector}")
        print(f"Pool Size: Brown={len(brown_pool)}, Green={len(green_pool)}")
    
    # ... (logica di check n_brown / n_green e random.sample è corretta) ...
    
    # Check if we have enough stocks
        n_brown = min(len(brown_pool), n_brown)
        n_green = min(len(green_pool), n_green)
    
    # Randomly select stocks from pools
        brown_stocks = random.sample(brown_pool['ticker'].tolist(), n_brown)
        green_stocks = random.sample(green_pool['ticker'].tolist(), n_green)
    # 4. STAMPA FINALE E RITORNO
        brown_scores = brown_pool['environment_score']
        green_scores = green_pool['environment_score']

        print(f"\n{'='*60}")
        print(f"RANDOMLY SELECTED {len(brown_stocks)} BROWN STOCKS (low Environment Score):")
        print(f"{'='*60}")
        for ticker in brown_stocks:
        # Usa il DataFrame filtrato 'sector_df' per trovare i dettagli
          stock_data = sector_df[sector_df['ticker'] == ticker].iloc[0]
          print(f"  {ticker:6s} - Env Score: {stock_data['environment_score']:5.2f} - {stock_data['sector']}")
        print(f"\nBrown Environment Score range: {brown_scores.min():.2f} - {brown_scores.max():.2f}")


        print(f"\n{'='*60}")
        print(f"RANDOMLY SELECTED {len(green_stocks)} GREEN STOCKS (high Environment Score):")
        print(f"{'='*60}")
        for ticker in green_stocks:
        # Usa il DataFrame filtrato 'sector_df' per trovare i dettagli
           stock_data = sector_df[sector_df['ticker'] == ticker].iloc[0]
           print(f"  {ticker:6s} - Env Score: {stock_data['environment_score']:5.2f} - {stock_data['sector']}")
        print(f"\nGreen Environment Score range: {green_scores.min():.2f} - {green_scores.max():.2f}")
        return {
          'brown': brown_stocks,
          'green': green_stocks,
          'brown_pool_size': len(brown_pool),
          'green_pool_size': len(green_pool),
          'brown_threshold': brown_threshold,
          'green_threshold': green_threshold # Ora definite nello scope corretto
        }

    
    def close(self):
        """Close Refinitiv session."""
        try:
            rd.close_session()
            print("\n✓ Refinitiv Data Platform session closed")
        except:
            pass


class ESGDataFetcher:
    """Fetch price data for ESG-selected stocks from Yahoo Finance."""
    
    def __init__(self, start_date: str = "2015-01-01", end_date: str = "2024-12-31"):
        self.start_date = start_date
        self.end_date = end_date
    
    def fetch_stock(self, ticker: str) -> pd.Series:
        """
        Download adjusted close price for a single stock.
        
        Args:
            ticker: Stock symbol
        
        Returns:
            Series with adjusted close prices
        """
        try:
            data = yf.download(ticker, start=self.start_date, end=self.end_date, 
                             auto_adjust=True, progress=False)
            return data['Close']
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return pd.Series(dtype=float)
    
    def fetch_multiple_stocks(self, tickers: List[str]) -> pd.DataFrame:
        """
        Download multiple stocks at once.
        
        Args:
            tickers: List of stock symbols
        
        Returns:
            DataFrame with one column per ticker

        """
        
        try:
            print(f"\nDownloading price data from Yahoo Finance for {len(tickers)} stocks...")
            data = yf.download(tickers, start=self.start_date, end=self.end_date,
                             auto_adjust=True, progress=False)['Close']
            
            # Handle single vs multiple tickers
            if isinstance(data, pd.Series):
                data = data.to_frame(tickers[0])
            
            df = data.dropna()
            print(f"✓ Successfully downloaded data: {df.shape[0]} days, {df.shape[1]} stocks")
            
            return df
        except Exception as e:
            print(f"Error fetching multiple stocks: {e}")
            return pd.DataFrame()
    
    def fetch_brown_green_data(self, stock_dict: Dict[str, List[str]]) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Fetch data for both Brown and Green stocks separately.
        
        Args:
            stock_dict: Dictionary with 'brown' and 'green' ticker lists
        
        Returns:
            Tuple of (brown_df, green_df)
        """
        brown_df = self.fetch_multiple_stocks(stock_dict['brown'])
        green_df = self.fetch_multiple_stocks(stock_dict['green'])
        
        return brown_df, green_df


# Example usage workflow
def main():
    """
    Complete workflow: ESG selection from Refinitiv API + price data from Yahoo Finance.
    """
    print("="*60)
    print("ESG-BASED STOCK SELECTION WORKFLOW")
    print("Using Refinitiv Data Platform API for ESG data")
    print("="*60)
    
    try:
        # Step 1: Initialize selector with Refinitiv API
        selector = RefinitivESGSelector(config_file="refinitiv-data.config")
        
        # Step 2: Fetch ESG scores from Refinitiv
        # For testing with a small subset:
        # test_tickers = selector.sp500_tickers[:50]
        # esg_df = selector.fetch_esg_scores(test_tickers)
        
        esg_df = selector.fetch_esg_scores()  # Full S&P 500
        
        # Check if we have enough data
        if len(esg_df) == 0:
            print("\n❌ ERROR: No ESG data available. Cannot proceed.")
            selector.close()
            return None, None, None, None
        
        if len(esg_df) < 30:
            print(f"\n⚠️  WARNING: Only {len(esg_df)} stocks with ESG data found.")
        
        # Save Environment scores
        esg_df.to_csv('environment_scores_refinitiv.csv', index=False)
        print("\n✓ Environment scores saved to 'environment_scores_refinitiv.csv'")
        
        # Step 3: Select Brown and Green stocks RANDOMLY
        selected_stocks = selector.select_brown_green_stocks(
            esg_df, 
            n_brown=15, 
            n_green=15,
            energy_focus=True,
            brown_percentile=0.25,  # Select from worst 25%
            green_percentile=0.75,   # Select from best 25%
            random_seed=None        # Set to integer for reproducibility
        )
        
        # Step 4: Fetch price data from Yahoo Finance
        fetcher = ESGDataFetcher(start_date="2015-01-01", end_date="2024-12-31")

        all_tickers = selected_stocks['brown'] + selected_stocks['green']
        df = fetcher.fetch_multiple_stocks(all_tickers)
        brown_df, green_df = fetcher.fetch_brown_green_data(selected_stocks)
        
        # Step 5: Save price data
        df.to_csv('combined_stocks_prices.csv')
        brown_df.to_csv('brown_stocks_prices.csv')
        green_df.to_csv('green_stocks_prices.csv')
        
        print("\n" + "="*60)
        print("WORKFLOW COMPLETE")
        print("="*60)
        print(f"Brown stocks data: {brown_df.shape}")
        print(f"Green stocks data: {green_df.shape}")
        print("\nFiles saved:")
        print("- environment_scores_refinitiv.csv")
        print("- brown_stocks_prices.csv")
        print("- green_stocks_prices.csv")
        
        # Close Refinitiv session
        selector.close()
        
        return esg_df, selected_stocks, brown_df, green_df, df
        
    except Exception as e:
        print(f"\n❌ ERROR in workflow: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, None


if __name__ == "__main__":
    # Run the complete workflow
    esg_df, ENERGY_STOCKS, brown_df, green_df, df = main()
    
    # Optional: Display summary statistics
    if esg_df is not None and not esg_df.empty:
        print("\n" + "="*60)
        print("ENVIRONMENT SCORE SUMMARY STATISTICS")
        print("="*60)
        print("\nBy Sector:")
        print(esg_df.groupby('sector')['environment_score'].describe())
        
        print("\n" + "="*60)
        print("TOP 10 WORST ENVIRONMENT SCORES:")
        print("="*60)
        worst = esg_df.nsmallest(10, 'environment_score')[['ticker', 'sector', 'environment_score']]
        print(worst.to_string(index=False))
        
        print("\n" + "="*60)
        print("TOP 10 BEST ENVIRONMENT SCORES:")
        print("="*60)
        best = esg_df.nlargest(10, 'environment_score')[['ticker', 'sector', 'environment_score']]
        print(best.to_string(index=False))


