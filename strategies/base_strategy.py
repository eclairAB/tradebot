from abc import ABC, abstractmethod
import pandas as pd
from broker import AlpacaBroker


class BaseStrategy(ABC):
    """
    All custom strategies must inherit from this class and implement `run()`.

    Example:
        class MyStrategy(BaseStrategy):
            def run(self):
                # fetch data, decide, place orders
                pass
    """

    def __init__(self, broker: AlpacaBroker, symbol: str, equity_pct: float = 0.1):
        self.broker = broker
        self.symbol = symbol
        self.equity_pct = equity_pct  # fraction of portfolio to deploy per trade

    def get_trade_qty(self) -> float:
        account = self.broker.get_account()
        buying_power = float(account.buying_power)
        price = self.broker.get_latest_price(self.symbol)
        budget = buying_power * self.equity_pct
        qty = int(budget // price)
        return max(qty, 1)

    @abstractmethod
    def run(self):
        """Execute one iteration of the strategy."""
        pass
