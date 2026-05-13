"""
Webhook server — receives signals from n8n and queues them for the bot.
Runs in a background thread alongside the main scheduler.

Endpoint: POST /signal
Payload:
  {
    "symbol": "AAPL",
    "sentiment": "positive" | "negative" | "neutral",
    "score": 0.85,        # -1.0 (most negative) to 1.0 (most positive)
    "headline": "Apple beats earnings expectations"
  }
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from queue import Queue
import uvicorn
import threading
from logger import log

app = FastAPI(title="Tradebot Signal Webhook")

# Shared queue — webhook pushes, strategy consumer pulls
signal_queue: Queue = Queue()

BUY_THRESHOLD = 0.6
SELL_THRESHOLD = -0.6


class SignalPayload(BaseModel):
    symbol: str
    sentiment: str
    score: float
    headline: str = ""

    @field_validator("score")
    @classmethod
    def score_in_range(cls, v):
        if not -1.0 <= v <= 1.0:
            raise ValueError("score must be between -1.0 and 1.0")
        return v

    @field_validator("symbol")
    @classmethod
    def symbol_upper(cls, v):
        return v.upper().strip()


@app.post("/signal")
def receive_signal(payload: SignalPayload):
    if payload.score >= BUY_THRESHOLD:
        action = "buy"
    elif payload.score <= SELL_THRESHOLD:
        action = "sell"
    else:
        action = "hold"

    log.info(
        f"[Webhook] Signal received — {payload.symbol} | "
        f"sentiment: {payload.sentiment} | score: {payload.score:.2f} | "
        f"action: {action} | headline: '{payload.headline}'"
    )

    if action != "hold":
        signal_queue.put({"symbol": payload.symbol, "action": action, "score": payload.score})

    return {"status": "ok", "action": action}


@app.get("/health")
def health():
    return {"status": "running", "queued_signals": signal_queue.qsize()}


def start_webhook_server(host: str = "0.0.0.0", port: int = 8000):
    def _run():
        uvicorn.run(app, host=host, port=port, log_level="warning")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    log.info(f"Webhook server listening on http://{host}:{port}/signal")
