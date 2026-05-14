"""
Omni-Downloader Pro — Main Entry Point
FastAPI + Telegram Webhook (Production-ready for Render)
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from telegram import Update
from telegram.ext import Application

from dotenv import load_dotenv
from handlers import setup_handlers

load_dotenv()

# ─── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── Config ─────────────────────────────────────────────────────────────────
BOT_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"].rstrip("/")   # e.g. https://your-app.onrender.com
PORT        = int(os.getenv("PORT", 8000))

# ─── Build Telegram Application ─────────────────────────────────────────────
application = Application.builder().token(BOT_TOKEN).build()
setup_handlers(application)

# ─── Lifespan (startup / shutdown) ──────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await application.initialize()
    await application.start()

    webhook_endpoint = f"{WEBHOOK_URL}/{BOT_TOKEN}"
    await application.bot.set_webhook(
        url=webhook_endpoint,
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )
    logger.info(f"✅ Webhook registered → {webhook_endpoint}")
    yield

    # Shutdown
    await application.bot.delete_webhook()
    await application.stop()
    await application.shutdown()
    logger.info("🛑 Bot stopped cleanly.")


# ─── FastAPI App ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Omni-Downloader Pro",
    description="AI-powered video downloader bot (Telegram)",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {
        "status": "running",
        "bot":    "Omni-Downloader Pro",
        "version": "1.0.0",
        "powered_by": ["yt-dlp", "Gemini AI", "Telegram Bot API"],
    }


@app.get("/health")
async def health():
    """Render uses this endpoint for health checks."""
    return {"status": "healthy"}


@app.post(f"/{BOT_TOKEN}")
async def telegram_webhook(request: Request):
    """Receive updates from Telegram."""
    payload = await request.json()
    update  = Update.de_json(payload, application.bot)
    await application.process_update(update)
    return Response(status_code=200)
