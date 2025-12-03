import praw
import pandas as pd
from datetime import datetime
import os
from pathlib import Path
import time
from dotenv import load_dotenv

load_dotenv()

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD")

TARGET_SUBREDDITS = [
    'investing', 'stocks', 'StockMarket', 'finance', 'SecurityAnalysis', 
    'ValueInvesting', 'energy', 'RenewableEnergy', 'solarenergy', 
    'cleanenergy', 'greeninvestor', 'wallstreetbets', 'options'
]

TRADING_ASSETS = {
    # Pair 1: NEE / CWEN
    "NEE": ["NextEra Energy", "NextEra", "$NEE", "NEE stock"],
    "CWEN": ["Clearway Energy", "Clearway", "$CWEN", "CWEN stock"],
    
    # Pair 2: RUN / PBW
    "RUN": ["Sunrun", "$RUN", "RUN stock"],
    "PBW": ["Invesco Clean Energy", "PBW", "WilderHill Clean Energy", "$PBW"],
    
    # Pair 3: PLUG / RUN (RUN is already covered above)
    "PLUG": ["Plug Power", "$PLUG", "PLUG stock"]
}

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
os.makedirs(DATA_DIR, exist_ok=True)

def classify_post_by_ticker(title: str, selftext: str) -> str | None:
    """
    Checks if a post mentions one of our specific trading assets.
    Returns the Ticker (e.g., 'NEE') if found, otherwise None.
    """
    search_text = (str(title) + " " + str(selftext)).lower()
    
    # Iterate through our assets to find a match
    for ticker, keywords in TRADING_ASSETS.items():
        for key in keywords:
            # We search for the keyword in lowercase
            if key.lower() in search_text:
                return ticker
                
    return None

def download_specific_pairs_data(subreddits: list[str], limit_per_keyword: int = 100):
    """
    Downloads posts specifically relevant to the trading pairs.
    """
    try:
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID, 
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT, 
            username=REDDIT_USERNAME, 
            password=REDDIT_PASSWORD
        )
        print(f"✅ Connected to Reddit API as: {reddit.user.me()}")
    except Exception as e:
        print(f"❌ CRITICAL ERROR: Could not connect to Reddit API: {e}")
        return None

    all_posts = {} 
    
    print(f"\n🔍 Starting targeted acquisition for: {list(TRADING_ASSETS.keys())}")

    # Iterate through every Ticker and every Keyword for that ticker
    for ticker, keywords in TRADING_ASSETS.items():
        print(f"\n--- Searching for Asset: {ticker} ---")
        
        for keyword in keywords:
            print(f"   > Keyword: '{keyword}'")
            
            for subreddit_name in subreddits:
                try:
                    subreddit = reddit.subreddit(subreddit_name)
                    # Search for the specific keyword
                    submissions = list(subreddit.search(keyword, limit=limit_per_keyword, sort="new"))
                    
                    if submissions:
                        for sub in submissions:
                            # Avoid duplicates
                            if sub.id not in all_posts:
                                # Double check classification
                                found_ticker = classify_post_by_ticker(sub.title, sub.selftext)
                                
                                # Only save if it matches one of our assets
                                if found_ticker:
                                    all_posts[sub.id] = {
                                        'id': sub.id, 
                                        'created_utc': datetime.fromtimestamp(sub.created_utc),
                                        'subreddit': subreddit_name, 
                                        'title': sub.title, 
                                        'selftext': sub.selftext,
                                        'score': sub.score, 
                                        'num_comments': sub.num_comments,
                                        'url': sub.url,
                                        'target_company': found_ticker, # e.g. "NEE"
                                        'theme': 'Trading_Pair_Asset'
                                    }
                    # Sleep slightly to respect API limits
                    time.sleep(0.5) 
                except Exception as e:
                    continue # Skip if subreddit issues
            
    if not all_posts:
        print("\n⚠️ No posts found for these specific assets.")
        return None

    # Convert to DataFrame
    final_df = pd.DataFrame(list(all_posts.values()))
    final_df.sort_values(by='created_utc', ascending=False, inplace=True)
    
    # Save as reddit_raw.csv (The name your agents expect!)
    output_filename = DATA_DIR / "reddit_raw.csv"
    
    print(f"\n💾 Saving {len(final_df)} targeted posts to: {output_filename.resolve()}")
    final_df.to_csv(output_filename, index=False, encoding='utf-8')
    
    return final_df

if __name__ == "__main__":
    # Run the targeted scraper
    df = download_specific_pairs_data(TARGET_SUBREDDITS, limit_per_keyword=50)
    
    if df is not None:
        print("\n📊 Data Acquisition Summary:")
        print(df['target_company'].value_counts())
        print("\n✅ Ready for CrewAI Integration!")