from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import pandas as pd
import config
from logger import log


class AlpacaBroker:
    def __init__(self):
        self.trading = TradingClient(
            config.ALPACA_API_KEY,
            config.ALPACA_SECRET_KEY,
            paper=(config.TRADING_MODE != "live"),
        )
        self.data = StockHistoricalDataClient(
            config.ALPACA_API_KEY,
            config.ALPACA_SECRET_KEY,
        )

    def get_account(self):
        return self.trading.get_account()

    def get_bars(self, symbol: str, timeframe: TimeFrame, days: int = 60) -> pd.DataFrame:
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=timeframe,
            start=datetime.now() - timedelta(days=days),
            end=datetime.now(),
        )
        bars = self.data.get_stock_bars(request)
        df = bars.df
        if isinstance(df.index, pd.MultiIndex):
            df = df.loc[symbol]
        return df.reset_index()

    def get_position(self, symbol: str):
        try:
            return self.trading.get_open_position(symbol)
        except Exception:
            return None

    def place_market_order(self, symbol: str, qty: float, side: str) -> dict:
        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        request = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=TimeInForce.DAY,
        )
        order = self.trading.submit_order(request)
        log.info(f"  Order submitted: {side.upper()} {qty} {symbol} (id: {order.id})")
        return order

    def close_position(self, symbol: str):
        try:
            self.trading.close_position(symbol)
            log.info(f"  Position closed: {symbol}")
        except Exception as e:
            log.warning(f"  Could not close position for {symbol}: {e}")

    def get_latest_price(self, symbol: str) -> float:
        df = self.get_bars(symbol, TimeFrame.Minute, days=1)
        if df.empty:
            raise ValueError(f"No price data returned for {symbol}")
        return float(df["close"].iloc[-1])
