"""
News Sentiment Strategy
------------------------
Consumes signals pushed by n8n via the webhook server.
Uses FinBERT (locally on-device) to score headlines if n8n sends raw text
instead of a pre-scored payload.

Signal thresholds (also mirrored in webhook_server.py):
  score >= 0.6  → BUY
  score <= -0.6 → SELL
  in between    → hold
"""

from .base_strategy import BaseStrategy
from webhook_server import signal_queue
from logger import log


class NewsSentimentStrategy(BaseStrategy):
    """
    Processes queued signals from the n8n webhook.
    Call run() on a tight loop (e.g. every 1 minute) to drain the queue.
    """

    def run(self):
        if signal_queue.empty():
            return

        while not signal_queue.empty():
            signal = signal_queue.get()
            symbol = signal["symbol"]
            action = signal["action"]
            score = signal["score"]

            if symbol != self.symbol:
                # Put it back for another strategy instance to handle
                signal_queue.put(signal)
                break

            log.info(f"[NewsSentiment] {symbol} — acting on signal: {action} (score: {score:.2f})")
            position = self.broker.get_position(symbol)

            if action == "buy" and position is None:
                qty = self.get_trade_qty()
                log.info(f"[NewsSentiment] {symbol} — BUY {qty} shares")
                self.broker.place_market_order(symbol, qty, "buy")

            elif action == "sell" and position is not None:
                log.info(f"[NewsSentiment] {symbol} — SELL / close position")
                self.broker.close_position(symbol)

            else:
                log.info(f"[NewsSentiment] {symbol} — signal '{action}' but no action taken (position: {position is not None})")
