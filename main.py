"""
Tradebot — entry point
-----------------------
Edit WATCHLIST and strategy settings below.
Set TRADING_MODE=paper or TRADING_MODE=live in your .env file.
"""

import schedule
import time
from broker import AlpacaBroker
from strategies import MovingAverageCrossover
from logger import log

# ---------------------------------------------------------------------------
# CONFIGURATION — edit these
# ---------------------------------------------------------------------------

WATCHLIST = ["AAPL", "MSFT", "NVDA"]

# How often to run the MA strategy (minutes)
RUN_EVERY_MINUTES = 60

# ---------------------------------------------------------------------------

def is_market_open(broker: AlpacaBroker) -> bool:
    return broker.trading.get_clock().is_open


def run_strategies(broker: AlpacaBroker):
    log.info("=" * 50)
    if not is_market_open(broker):
        log.info("Market is closed — skipping run.")
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
            log.error(f"Strategy error for {symbol}: {e}")


def main():
    broker = AlpacaBroker()

    log.info(f"Bot started. Running every {RUN_EVERY_MINUTES}m.")
    log.info(f"Watching: {', '.join(WATCHLIST)}")

    run_strategies(broker)
    schedule.every(RUN_EVERY_MINUTES).minutes.do(run_strategies, broker=broker)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
