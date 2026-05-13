"""
News Fetcher + FinBERT Sentiment Scorer
----------------------------------------
Fetches RSS headlines for each watched symbol and scores them locally
using FinBERT (ProsusAI/finbert) — a financial sentiment model.

This runs as a standalone loop and POSTs scored signals to the webhook
server, so the same pipeline handles both n8n signals and local news.

FinBERT labels:  positive → +score, negative → -score, neutral → 0
"""

import feedparser
import requests
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from logger import log

WEBHOOK_URL = "http://localhost:8000/signal"

# RSS feeds — Yahoo Finance news per ticker
RSS_FEEDS = {
    "AAPL": "https://finance.yahoo.com/rss/headline?s=AAPL",
    "MSFT": "https://finance.yahoo.com/rss/headline?s=MSFT",
    "NVDA": "https://finance.yahoo.com/rss/headline?s=NVDA",
}

_tokenizer = None
_model = None


def _load_finbert():
    global _tokenizer, _model
    if _model is None:
        log.info("[NewsFetcher] Loading FinBERT model (first run may download ~500MB)...")
        _tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        _model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        _model.eval()
        log.info("[NewsFetcher] FinBERT loaded.")


def score_headline(headline: str) -> tuple[str, float]:
    """Returns (sentiment_label, score) where score is -1.0 to 1.0."""
    _load_finbert()
    inputs = _tokenizer(headline, return_tensors="pt", truncation=True, max_length=512)
    with torch.no_grad():
        logits = _model(**inputs).logits
    probs = torch.softmax(logits, dim=-1).squeeze()
    # FinBERT label order: positive, negative, neutral
    pos, neg, neu = probs[0].item(), probs[1].item(), probs[2].item()
    if pos > neg and pos > neu:
        return "positive", round(pos, 4)
    elif neg > pos and neg > neu:
        return "negative", round(-neg, 4)
    else:
        return "neutral", 0.0


def fetch_and_score(watchlist: list[str], seen_headlines: set):
    for symbol in watchlist:
        feed_url = RSS_FEEDS.get(symbol)
        if not feed_url:
            continue

        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:5]:  # latest 5 headlines
            headline = entry.get("title", "").strip()
            if not headline or headline in seen_headlines:
                continue

            seen_headlines.add(headline)
            sentiment, score = score_headline(headline)
            log.info(f"[NewsFetcher] {symbol} | {sentiment} ({score:+.2f}) | {headline}")

            if abs(score) >= 0.6:
                try:
                    requests.post(WEBHOOK_URL, json={
                        "symbol": symbol,
                        "sentiment": sentiment,
                        "score": score,
                        "headline": headline,
                    }, timeout=5)
                except Exception as e:
                    log.warning(f"[NewsFetcher] Failed to post signal: {e}")
