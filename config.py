import os
from dotenv import load_dotenv

load_dotenv()

TRADING_MODE = os.getenv("TRADING_MODE", "paper").lower()

if TRADING_MODE == "live":
    ALPACA_API_KEY = os.getenv("ALPACA_LIVE_API_KEY")
    ALPACA_SECRET_KEY = os.getenv("ALPACA_LIVE_SECRET_KEY")
    ALPACA_BASE_URL = "https://api.alpaca.markets"
    print("⚠️  LIVE TRADING MODE ACTIVE — real money will be used")
else:
    ALPACA_API_KEY = os.getenv("ALPACA_PAPER_API_KEY")
    ALPACA_SECRET_KEY = os.getenv("ALPACA_PAPER_SECRET_KEY")
    ALPACA_BASE_URL = "https://paper-api.alpaca.markets"
    print("📄 Paper trading mode active (simulation)")

if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
    raise EnvironmentError(
        f"Missing Alpaca API keys for '{TRADING_MODE}' mode. "
        "Copy .env.example to .env and fill in your credentials."
    )
