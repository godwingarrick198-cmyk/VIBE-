from __future__ import annotations
import asyncio,logging
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import Application,CommandHandler,ContextTypes
from app.config import settings
from app.deriv import DerivClient,DerivAPIError
from app.gemini_signal import GeminiSignalAnalyzer,AnalysisError
from app.indicators import candle_features
from app.market_data import TwelveDataClient,MarketDataError
from app.risk import RiskState
log=logging.getLogger(__name__)

class TradingAgent:
 def __init__(self):
  self.mode="demo";self.execution_enabled=False;self.live_confirmation_pending=False
  self.risk=RiskState(settings.profit_target,settings.max_session_loss,settings.session_hours,settings.max_trades_per_session,settings.max_consecutive_losses)
  self.market=TwelveDataClient(settings.twelve_data_api_key);self.analyzer=GeminiSignalAnalyzer(settings.gemini_api_key,settings.gemini_model)
  self.signals=[];self.trades=[];self.last_cycle="Not run yet";self.last_error="";self.base_stake_override=settings.base_stake
 def deriv(self):
  return DerivClient(settings.deriv_app_id,settings.deriv_demo_token if self.mode=="demo" else settings.deriv_real_token)
 def status_text(self):
  allowed,reason=self.risk.can_trade() if self.execution_enabled and settings.auto_trade else (False,"Execution disabled by control or AUTO_TRADE=false")
  return (f"VIBE AI Trading Agent\nMode: {self.mode.upper()}\nExecution: {'ON' if self.execution_enabled and settings.auto_trade and allowed else 'OFF'} ({reason})\nExpiry: {settings.default_expiry_minutes} minute(s)\nSession P/L: {self.risk.pnl:+.2f} {settings.deriv_currency}\nTrades: {self.risk.trades}/{self.risk.max_trades}\nProfit target: {self.risk.profit_target:.2f}\nMaximum loss: {abs(self.risk.max_session_loss):.2f}\nLast analysis: {self.last_cycle}\nLast error: {self.last_error or 'None'}")
 async def send_owner(self,app,text):
  if settings.telegram_chat_id:
   try:await app.bot.send_message(chat_id=settings.telegram_chat_id,text=text)
   except Exception:log.exception("Could not send configured chat notification")
 async def cycle(self,app):
  self.last_cycle=datetime.now().isoformat(timespec="seconds");candidates=[]
  for asset in settings.assets:
   try:
    candles=await self.market.candles(asset.twelve_symbol,"5min",120)
    result=await self.analyzer.analyze(asset.twelve_symbol,candle_features(candles))
    if result["confidence"]>=settings.min_confidence:candidates.append({**result,"twelve_symbol":asset.twelve_symbol,"deriv_symbol":asset.deriv_symbol})
   except (MarketDataError,AnalysisError,ValueError) as exc:
    self.last_error=f"{asset.twelve_symbol}: {exc}";log.warning("Skipping %s: %s",asset.twelve_symbol,exc)
   except Exception as exc:
    self.last_error=f"{asset.twelve_symbol}: {exc}";log.exception("Unexpected analysis error")
  if not candidates:log.info("No qualifying signal; no WAIT message is sent.");return
  best=max(candidates,key=lambda x:x["confidence"]);now=datetime.now(ZoneInfo(settings.timezone))
  signal={**best,"created_at":now.isoformat(),"entry_time":now.strftime("%I:%M %p").lstrip("0"),"expiry_minutes":settings.default_expiry_minutes}
  self.signals.insert(0,signal);self.signals=self.signals[:20]
  await self.send_owner(app,self.format_signal(signal))
  allowed,reason=self.risk.can_trade()
  if settings.auto_trade and self.execution_enabled and allowed:await self.execute_signal(app,signal)
  elif settings.auto_trade and self.execution_enabled and not allowed:
   self.execution_enabled=False;self.risk.enabled=False;await self.send_owner(app,f"Execution stopped: {reason}")
 def format_signal(self,s):
  start=datetime.fromisoformat(s["created_at"]).astimezone(ZoneInfo(settings.timezone))
  levels=[f"• Level {i} → {(start+timedelta(minutes=s['expiry_minutes']*i)).strftime('%I:%M %p').lstrip('0')}" for i in range(1,settings.martingale_max_levels+1)]
  return ("🚨 TRADE NOW!!\n\n"+f"📊 {s['twelve_symbol']}\n🕒 Expiry: {s['expiry_minutes']}-minute contract\n🤖 Model score: {s['confidence']}% (not a probability)\n🕰 Entry window: {s['entry_time']}\n📉 Direction: {'🟢 BUY' if s['direction']=='BUY' else '🔴 SELL'}\n🧠 Reason: {s['rationale']}\n\n📊 Martingale schedule (display only; auto-recovery OFF):\n"+("\n".join(levels) if levels else "Disabled"))
 async def execute_signal(self,app,s):
  allowed,reason=self.risk.can_trade()
  if not allowed: self.execution_enabled=False;await self.send_owner(app,f"Order blocked by risk guard: {reason}");return
  if self.mode=="live" and (not settings.enable_live_trading or not settings.deriv_real_token):
   self.execution_enabled=False;await self.send_owner(app,"Live order blocked: live trading is locked in environment settings.");return
  stake=min(self.base_stake_override,settings.max_stake)
  try:
   result=await self.deriv().buy_direction(s["deriv_symbol"],s["direction"],stake,s["expiry_minutes"],settings.deriv_currency)
   trade={**result,"created_at":datetime.now().isoformat(timespec="seconds"),"direction":s["direction"],"stake":stake,"status":"OPEN","profit":None}
   self.trades.insert(0,trade);self.trades=self.trades[:50]
   await self.send_owner(app,f"✅ DEMO/TRADE ORDER ACCEPTED\nMode: {self.mode.upper()}\nAsset: {s['twelve_symbol']}\nDirection: {s['direction']}\nStake: {stake:.2f}\nContract ID: {result['contract_id']}\nExpiry: {s['expiry_minutes']} minutes")
   asyncio.create_task(self.monitor_trade(app,trade,s["expiry_minutes"]))
  except DerivAPIError as exc:self.last_error=str(exc);await self.send_owner(app,f"❌ Deriv execution failed: {exc}")
 async def monitor_trade(self,app,trade,expiry):
  await asyncio.sleep(expiry*60+5)
  try:
   status={}
   for i in range(6):
    status=await self.deriv().contract_status(trade["contract_id"]);state=str(status.get("status","")).lower()
    if status.get("is_sold") or status.get("is_expired") or state in {"won","lost","sold"}:break
    if i<5:await asyncio.sleep(10)
   state=str(status.get("status","")).lower()
   if not(status.get("is_sold") or status.get("is_expired") or state in {"won","lost","sold"}):raise RuntimeError("Contract has not reached a confirmed settled state")
   profit=float(status.get("profit",0));trade["status"]=state.upper();trade["profit"]=profit;self.risk.record_result(profit)
   allowed,reason=self.risk.can_trade()
   if not allowed:self.execution_enabled=False;self.risk.enabled=False;await self.send_owner(app,f"🛑 Execution stopped: {reason}")
   await self.send_owner(app,f"🏁 TRADE RESULT\nAsset: {trade['symbol']}\nDirection: {trade['direction']}\nResult: {profit:+.2f} {settings.deriv_currency}\nSession P/L: {self.risk.pnl:+.2f} {settings.deriv_currency}\nStatus: {trade['status']}")
  except Exception as exc:
   self.last_error=f"Could not verify contract result: {exc}";log.exception("Trade monitor failed")
   await self.send_owner(app,f"⚠️ Could not verify contract {trade['contract_id']}: {exc}. Check Deriv manually.")

def authorized(update):
 return bool(update.effective_user and settings.telegram_owner_id and update.effective_user.id==settings.telegram_owner_id)
async def guard(update):
 if not authorized(update):
  if update.effective_message:await update.effective_message.reply_text("Unauthorized. Set TELEGRAM_OWNER_ID to your numeric Telegram user ID.")
  return False
 return True
async def start(update,context):
 if await guard(update):await update.effective_message.reply_text("VIBE is online. Execution is OFF by default. Commands: /status /demo /live /confirm_live YES /stop /resume /balance /target 20 /maxloss 5 /stake 1 /signals /trades /pnl")
async def status(update,context):
 if await guard(update):await update.effective_message.reply_text(context.application.bot_data["agent"].status_text())
async def demo(update,context):
 if not await guard(update):return
 a=context.application.bot_data["agent"];a.mode="demo";a.execution_enabled=False;a.risk.enabled=False;a.live_confirmation_pending=False
 await update.effective_message.reply_text("Switched to DEMO. Execution OFF; use /resume to start a fresh session.")
async def live(update,context):
 if not await guard(update):return
 a=context.application.bot_data["agent"]
 if not settings.enable_live_trading or not settings.deriv_real_token:
  await update.effective_message.reply_text("Live mode locked. Configure ENABLE_LIVE_TRADING=true and DERIV_REAL_TOKEN in Render first.");return
 a.execution_enabled=False;a.risk.enabled=False;a.live_confirmation_pending=True
 await update.effective_message.reply_text("⚠️ Live trading can lose real money. Confirm only if intended: /confirm_live YES")
async def confirm_live(update,context):
 if not await guard(update):return
 a=context.application.bot_data["agent"]
 if not a.live_confirmation_pending or not context.args or context.args[0].upper()!="YES" or not settings.enable_live_trading or not settings.deriv_real_token:
  await update.effective_message.reply_text("Not confirmed. Use /live first, then /confirm_live YES.");return
 a.mode="live";a.live_confirmation_pending=False;a.risk.reset_session();a.execution_enabled=True
 await update.effective_message.reply_text("LIVE mode confirmed. Orders remain subject to risk limits. /stop halts new orders.")
async def stop(update,context):
 if not await guard(update):return
 a=context.application.bot_data["agent"];a.execution_enabled=False;a.risk.enabled=False
 await update.effective_message.reply_text("🛑 New orders stopped. Existing contracts are not automatically closed.")
async def resume(update,context):
 if not await guard(update):return
 a=context.application.bot_data["agent"]
 if not settings.auto_trade:
  await update.effective_message.reply_text("AUTO_TRADE=false: signal-only mode. Set it true in Render and redeploy to permit orders.");return
 if a.mode=="live":
  await update.effective_message.reply_text("For live mode, use /stop, then /live and /confirm_live YES.");return
 a.risk.reset_session();a.execution_enabled=True
 await update.effective_message.reply_text("Demo execution enabled for a fresh risk session.")
async def balance(update,context):
 if not await guard(update):return
 try:
  v=await context.application.bot_data["agent"].deriv().balance();await update.effective_message.reply_text(f"Deriv balance: {v.get('balance','unknown')} {v.get('currency',settings.deriv_currency)}")
 except Exception as exc:await update.effective_message.reply_text(f"Could not read Deriv balance: {exc}")
async def set_amount(update,context,field):
 if not await guard(update):return
 try:v=float(context.args[0]);assert v>0
 except (ValueError,IndexError,AssertionError):
  await update.effective_message.reply_text("Supply a positive number.");return
 a=context.application.bot_data["agent"]
 if field=="target":a.risk.profit_target=v;reply=f"Profit target: {v:.2f} {settings.deriv_currency}"
 elif field=="maxloss":a.risk.max_session_loss=v;reply=f"Maximum loss: {v:.2f} {settings.deriv_currency}"
 elif v>settings.max_stake:
  await update.effective_message.reply_text(f"Stake exceeds MAX_STAKE ({settings.max_stake:.2f}).");return
 else:a.base_stake_override=v;reply=f"Base stake set to {v:.2f} {settings.deriv_currency} for this process."
 await update.effective_message.reply_text(reply)
async def target(update,context):await set_amount(update,context,"target")
async def maxloss(update,context):await set_amount(update,context,"maxloss")
async def stake(update,context):await set_amount(update,context,"stake")
async def signals(update,context):
 if not await guard(update):return
 rows=context.application.bot_data["agent"].signals
 await update.effective_message.reply_text("\n".join(f"{x['created_at']} | {x['twelve_symbol']} | {x['direction']} | model score {x['confidence']}%" for x in rows[:10]) if rows else "No qualifying BUY/SELL signals yet.")
async def trades(update,context):
 if not await guard(update):return
 rows=context.application.bot_data["agent"].trades
 lines=[f"{x['created_at']} | {x['symbol']} | {x['direction']} | {x['status']} | {'pending' if x['profit'] is None else f'{x['profit']:+.2f}'}" for x in rows[:10]]
 await update.effective_message.reply_text("\n".join(lines) if lines else "No trades recorded in this process.")
async def pnl(update,context):
 if await guard(update):
  a=context.application.bot_data["agent"];await update.effective_message.reply_text(f"Session P/L: {a.risk.pnl:+.2f} {settings.deriv_currency}")
async def signal_loop(app,agent):
 await asyncio.sleep(10)
 while True:
  try:await agent.cycle(app)
  except Exception as exc:agent.last_error=str(exc);log.exception("Signal cycle failed")
  await asyncio.sleep(settings.signal_interval_seconds)
def build_bot():
 if not settings.telegram_bot_token:raise RuntimeError("TELEGRAM_BOT_TOKEN is required")
 app=Application.builder().token(settings.telegram_bot_token).build()
 for name,handler in [("start",start),("help",start),("status",status),("demo",demo),("live",live),("confirm_live",confirm_live),("stop",stop),("resume",resume),("balance",balance),("target",target),("maxloss",maxloss),("stake",stake),("signals",signals),("trades",trades),("pnl",pnl)]:
  app.add_handler(CommandHandler(name,handler))
 return app
