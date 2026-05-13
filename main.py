"""
Tradebot — entry point
-----------------------
Edit WATCHLIST and ACTIVE_STRATEGY below to configure the bot.
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

# Stocks to trade (one strategy instance per symbol)
WATCHLIST = ["AAPL", "MSFT", "NVDA"]

# How often to run (minutes). Market hours only check is built-in.
RUN_EVERY_MINUTES = 60

# ---------------------------------------------------------------------------

def is_market_open(broker: AlpacaBroker) -> bool:
    clock = broker.trading.get_clock()
    return clock.is_open


def run_strategies(broker: AlpacaBroker):
    log.info("=" * 50)
    if not is_market_open(broker):
        log.info("Market is closed — skipping this run.")
        return

    account = broker.get_account()
    equity = float(account.equity)
    buying_power = float(account.buying_power)
    log.info(f"Account equity: ${equity:,.2f} | Buying power: ${buying_power:,.2f}")

    for symbol in WATCHLIST:
        strategy = MovingAverageCrossover(
            broker=broker,
            symbol=symbol,
            short_window=20,
            long_window=50,
            equity_pct=0.1,  # use up to 10% of buying power per trade
        )
        try:
            strategy.run()
        except Exception as e:
            log.error(f"ERROR running strategy for {symbol}: {e}")


def main():
    broker = AlpacaBroker()

    log.info(f"Bot started. Running every {RUN_EVERY_MINUTES} minute(s).")
    log.info(f"Watching: {', '.join(WATCHLIST)}")

    # Run immediately on start
    run_strategies(broker)

    # Then on schedule
    schedule.every(RUN_EVERY_MINUTES).minutes.do(run_strategies, broker=broker)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
