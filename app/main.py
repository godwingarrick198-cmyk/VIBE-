from __future__ import annotations
import asyncio,logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.bot import build_bot,TradingAgent,signal_loop
from app.config import settings
logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log=logging.getLogger(__name__)
@asynccontextmanager
async def lifespan(app):
 bot=None;task=None;updater_started=False;bot_started=False
 if settings.telegram_bot_token:
  bot=build_bot();await bot.initialize();agent=TradingAgent();bot.bot_data["agent"]=agent
  task=asyncio.create_task(signal_loop(bot,agent))
  await bot.start();bot_started=True
  if bot.updater:await bot.updater.start_polling(drop_pending_updates=True);updater_started=True
  log.info("Telegram polling started; execution OFF by default")
 else:log.warning("TELEGRAM_BOT_TOKEN missing; health endpoint only")
 app.state.telegram_app=bot
 try:yield
 finally:
  if task:
   task.cancel()
   try:await task
   except asyncio.CancelledError:pass
  if bot:
   if updater_started and bot.updater:await bot.updater.stop()
   if bot_started:await bot.stop()
   await bot.shutdown()
app=FastAPI(title="VIBE AI Trading Agent",version="0.1.0",lifespan=lifespan)
@app.get("/")
async def root():return {"service":"VIBE AI Trading Agent","status":"running","execution_default":"OFF","live_trading_default":"LOCKED"}
@app.get("/health")
async def health():return {"status":"ok","telegram_configured":bool(settings.telegram_bot_token)}
