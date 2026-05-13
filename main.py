"""
Tradebot — entry point
-----------------------
Edit WATCHLIST, strategy settings, and feature flags below.
Set TRADING_MODE=paper or TRADING_MODE=live in your .env file.
"""

import schedule
import time
from broker import AlpacaBroker
from strategies import MovingAverageCrossover, NewsSentimentStrategy
from logger import log

# ---------------------------------------------------------------------------
# CONFIGURATION — edit these
# ---------------------------------------------------------------------------

WATCHLIST = ["AAPL", "MSFT", "NVDA"]

# How often to run the MA strategy (minutes)
RUN_EVERY_MINUTES = 60

# How often to drain the news signal queue (minutes)
NEWS_CHECK_EVERY_MINUTES = 1

# Feature flags
ENABLE_NEWS_SENTIMENT = True   # processes signals from n8n or local news fetcher
ENABLE_LOCAL_NEWS_FETCH = True  # run FinBERT RSS fetcher on-device (needs torch)
WEBHOOK_PORT = 8000

# ---------------------------------------------------------------------------

def is_market_open(broker: AlpacaBroker) -> bool:
    return broker.trading.get_clock().is_open


def run_ma_strategies(broker: AlpacaBroker):
    log.info("=" * 50)
    if not is_market_open(broker):
        log.info("Market is closed — skipping MA strategy run.")
        return

    account = broker.get_account()
    log.info(f"Equity: ${float(account.equity):,.2f} | Buying power: ${float(account.buying_power):,.2f}")

    for symbol in WATCHLIST:
        strategy = MovingAverageCrossover(
            broker=broker,
            symbol=symbol,
            short_window=20,
            long_window=50,
            equity_pct=0.1,
        )
        try:
            strategy.run()
        except Exception as e:
            log.error(f"MA strategy error for {symbol}: {e}")


def run_news_strategies(broker: AlpacaBroker):
    if not is_market_open(broker):
        return
    for symbol in WATCHLIST:
        try:
            NewsSentimentStrategy(broker=broker, symbol=symbol, equity_pct=0.1).run()
        except Exception as e:
            log.error(f"News sentiment error for {symbol}: {e}")


def main():
    broker = AlpacaBroker()

    # Start webhook server (receives signals from n8n)
    if ENABLE_NEWS_SENTIMENT:
        from webhook_server import start_webhook_server
        start_webhook_server(port=WEBHOOK_PORT)

    # Start local FinBERT news fetcher
    if ENABLE_LOCAL_NEWS_FETCH:
        import threading
        from news_fetcher import fetch_and_score
        seen_headlines: set = set()

        def _news_loop():
            while True:
                try:
                    fetch_and_score(WATCHLIST, seen_headlines)
                except Exception as e:
                    log.error(f"News fetcher error: {e}")
                time.sleep(NEWS_CHECK_EVERY_MINUTES * 60)

        threading.Thread(target=_news_loop, daemon=True).start()
        log.info(f"Local news fetcher started (checking every {NEWS_CHECK_EVERY_MINUTES}m)")

    log.info(f"Bot started. MA strategy runs every {RUN_EVERY_MINUTES}m.")
    log.info(f"Watching: {', '.join(WATCHLIST)}")

    # Run MA strategy immediately then on schedule
    run_ma_strategies(broker)
    schedule.every(RUN_EVERY_MINUTES).minutes.do(run_ma_strategies, broker=broker)

    # Drain news signal queue on tight loop
    if ENABLE_NEWS_SENTIMENT:
        schedule.every(NEWS_CHECK_EVERY_MINUTES).minutes.do(run_news_strategies, broker=broker)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
