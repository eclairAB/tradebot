# Tradebot

Automated stock trading bot using the [Alpaca](https://alpaca.markets) API. Supports paper (simulation) and live trading via a single config switch.

---

## Features

- Paper and live trading (switchable via `.env`)
- Modular strategy system — drop in your own strategies
- Logs to file and terminal (daily log files in `logs/`)
- Market hours check — skips runs when market is closed
- Runs on any machine including Raspberry Pi

---

## Project Structure

```
tradebot/
├── main.py                          # Entry point — configure watchlist here
├── config.py                        # Loads .env, switches paper/live mode
├── logger.py                        # Logging setup
├── requirements.txt
├── .env.example                     # Copy to .env and fill in API keys
├── broker/
│   └── alpaca_client.py             # Alpaca API wrapper
└── strategies/
    ├── base_strategy.py             # Base class for all strategies
    └── moving_average_crossover.py  # Starter strategy (golden/death cross)
```

---

## Setup

### 1. Get Alpaca API Keys

1. Sign up at [alpaca.markets](https://alpaca.markets)
2. Go to **Paper Trading → API Keys** and generate a key pair
3. For live trading, generate a separate key pair under **Live Trading**

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
ALPACA_PAPER_API_KEY=your_paper_key
ALPACA_PAPER_SECRET_KEY=your_paper_secret

ALPACA_LIVE_API_KEY=your_live_key
ALPACA_LIVE_SECRET_KEY=your_live_secret

# "paper" for simulation, "live" for real money
TRADING_MODE=paper
```

### 3. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run

```bash
python main.py
```

---

## Configuration

Edit the top of `main.py` to change which stocks to watch and how often to run:

```python
WATCHLIST = ["AAPL", "MSFT", "NVDA"]
RUN_EVERY_MINUTES = 60
```

---

## Switching to Live Trading

In `.env`, change:

```env
TRADING_MODE=live
```

> **Warning:** Live mode uses real money. The bot will print a warning on startup. Make sure you have tested your strategy thoroughly in paper mode first.

---

## Viewing P&L

Paper and live P&L are available in the Alpaca dashboard:

1. Log in at [app.alpaca.markets](https://app.alpaca.markets)
2. Select **Paper** or **Live** account from the top-left dropdown
3. Navigate to:
   - **Portfolio** — equity chart over time
   - **Positions** — open trades with unrealised P&L
   - **Orders** — every order the bot placed
   - **Account Activity** — realised P&L per closed trade

Logs are also written to `logs/tradebot_YYYY-MM-DD.log`.

---

## Adding a Custom Strategy

1. Create a new file in `strategies/`, e.g. `strategies/my_strategy.py`
2. Inherit from `BaseStrategy` and implement `run()`:

```python
from .base_strategy import BaseStrategy
from logger import log

class MyStrategy(BaseStrategy):
    def run(self):
        price = self.broker.get_latest_price(self.symbol)
        log.info(f"{self.symbol} price: {price}")
        # your logic here — use self.broker to place orders
```

3. Import and use it in `main.py`:

```python
from strategies import MyStrategy

strategy = MyStrategy(broker=broker, symbol=symbol)
strategy.run()
```

---

## Deploying on Raspberry Pi

```bash
git clone <your-repo-url>
cd tradebot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
python main.py
```

To keep it running after you close the terminal:

```bash
nohup python main.py &> logs/nohup.log &
```

Or set it up as a `systemd` service for auto-start on boot.

---

## Disclaimer

This bot is for educational purposes. Algorithmic trading involves financial risk. Always test in paper mode before using real money.
