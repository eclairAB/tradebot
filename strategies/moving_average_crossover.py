"""
Moving Average Crossover Strategy
----------------------------------
Signal logic:
  - BUY  when the short-term MA crosses ABOVE the long-term MA (golden cross)
  - SELL when the short-term MA crosses BELOW the long-term MA (death cross)

Default: 20-day SMA vs 50-day SMA on daily bars.
"""

import pandas as pd
from alpaca.data.timeframe import TimeFrame
from .base_strategy import BaseStrategy
from logger import log


class MovingAverageCrossover(BaseStrategy):
    def __init__(self, broker, symbol: str, short_window: int = 20, long_window: int = 50, equity_pct: float = 0.1):
        super().__init__(broker, symbol, equity_pct)
        self.short_window = short_window
        self.long_window = long_window

    def _compute_signals(self) -> pd.DataFrame:
        days_needed = self.long_window + 10
        df = self.broker.get_bars(self.symbol, TimeFrame.Day, days=days_needed)
        df["sma_short"] = df["close"].rolling(self.short_window).mean()
        df["sma_long"] = df["close"].rolling(self.long_window).mean()
        df["signal"] = 0
        df.loc[df["sma_short"] > df["sma_long"], "signal"] = 1   # bullish
        df.loc[df["sma_short"] < df["sma_long"], "signal"] = -1  # bearish
        df["crossover"] = df["signal"].diff()
        return df

    def run(self):
        log.info(f"[MovingAverageCrossover] Checking {self.symbol} ...")
        df = self._compute_signals()
        latest = df.iloc[-1]
        price = latest["close"]
        sma_s = round(latest["sma_short"], 2)
        sma_l = round(latest["sma_long"], 2)
        crossover = latest["crossover"]

        log.info(f"  {self.symbol} — Price: {price:.2f} | SMA{self.short_window}: {sma_s} | SMA{self.long_window}: {sma_l}")

        position = self.broker.get_position(self.symbol)

        if crossover > 0:  # golden cross → buy signal
            if position is None:
                qty = self.get_trade_qty()
                log.info(f"  {self.symbol} — Golden cross detected → BUY {qty} shares")
                self.broker.place_market_order(self.symbol, qty, "buy")
            else:
                log.info(f"  {self.symbol} — Golden cross detected but already holding — skipping")

        elif crossover < 0:  # death cross → sell signal
            if position is not None:
                log.info(f"  {self.symbol} — Death cross detected → SELL / close position")
                self.broker.close_position(self.symbol)
            else:
                log.info(f"  {self.symbol} — Death cross detected but no position — skipping")

        else:
            trend = "bullish" if latest["signal"] == 1 else "bearish" if latest["signal"] == -1 else "neutral"
            log.info(f"  {self.symbol} — No crossover, holding ({trend} trend)")
