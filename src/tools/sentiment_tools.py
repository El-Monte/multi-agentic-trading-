import pandas as pd
import os
import torch
from transformers import pipeline
from crewai.tools import tool
from typing import Dict
from pathlib import Path

SENTIMENT_PIPELINE = None

def get_sentiment_pipeline():
    global SENTIMENT_PIPELINE
    if SENTIMENT_PIPELINE is None:
        print("🧠 LOADING FINBERT AI MODEL... (This happens only once)")
        device = 0 if torch.cuda.is_available() else -1
        SENTIMENT_PIPELINE = pipeline("sentiment-analysis", model="ProsusAI/finbert", device=device)
    return SENTIMENT_PIPELINE

@tool("Analyze Reddit Sentiment")
def analyze_social_sentiment(ticker: str) -> Dict:
    """
    Uses a FinBERT AI model to analyze RAW Reddit posts for a specific ticker.
    It calculates a sentiment score from -1 (Negative) to +1 (Positive) in real-time.
    
    Args:
        ticker (str): The stock ticker (e.g., "ETR", "AEP", "ATO").
    """
    try:
        project_root = Path(__file__).resolve().parents[2] 
        file_path = project_root / "data" / "processed" / "reddit_raw.csv"
        
        print(f"\n Looking for sentiment data at: {file_path}")
        
        if not file_path.exists():
            return {
                "error": f"File not found at: {file_path}. Please run 'src/data/download_pairs_reddit.py' first.",
                "ticker": ticker,
                "score": 0.0
            }
            
        df = pd.read_csv(file_path)
        
        # Filter for the Ticker
        ticker_upper = ticker.upper().strip()
        
        relevant_posts = df[
            (df['target_company'].astype(str).str.upper() == ticker_upper) | 
            (df['title'].astype(str).str.upper().str.contains(ticker_upper, na=False))
        ].copy()
        
        if relevant_posts.empty:
            return {
                "ticker": ticker, 
                "sentiment": "NEUTRAL (No posts found)", 
                "score": 0.0,
                "note": f"No Reddit posts found for {ticker} in the database."
            }

        relevant_posts = relevant_posts.head(10)
        
        nlp = get_sentiment_pipeline()
        
        texts = []
        for _, row in relevant_posts.iterrows():
            text = str(row['title'])
            if 'selftext' in row and pd.notna(row['selftext']):
                text += " " + str(row['selftext'])
            texts.append(text[:512])
            
        results = nlp(texts)
        
        # Calculate Weighted Score
        score_map = {'positive': 1, 'negative': -1, 'neutral': 0}
        total_score = 0
        
        for res in results:
            val = score_map.get(res['label'], 0)
            total_score += val * res['score'] 
            
        avg_score = total_score / len(results)
        
        # Result Interpretation
        sentiment_label = "NEUTRAL"
        if avg_score > 0.15: sentiment_label = "BULLISH"
        if avg_score < -0.15: sentiment_label = "BEARISH"

        return {
            "ticker": ticker,
            "ai_tool_used": "FinBERT (ProsusAI)",
            "posts_analyzed": len(results),
            "sentiment_score": round(avg_score, 3),
            "sentiment_label": sentiment_label
        }

    except Exception as e:
        return {"error": f"AI Analysis failed: {str(e)}"}