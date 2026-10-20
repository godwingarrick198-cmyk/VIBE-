from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()
def _bool(n,d=False):
 v=os.getenv(n); return d if v is None else v.strip().lower() in {"1","true","yes","on"}
def _int(n,d):
 try:return int(os.getenv(n,str(d)))
 except (TypeError,ValueError):return d
def _float(n,d):
 try:return float(os.getenv(n,str(d)))
 except (TypeError,ValueError):return d
@dataclass(frozen=True)
class Asset:
 twelve_symbol:str
 deriv_symbol:str
def _assets():
 raw=os.getenv("ASSETS","EUR/USD:frxEURUSD,EUR/CHF:frxEURCHF,GBP/USD:frxGBPUSD,USD/JPY:frxUSDJPY,AUD/USD:frxAUDUSD,USD/CAD:frxUSDCAD"); out=[]
 for item in raw.split(","):
  if ":" in item:
   a,b=item.strip().split(":",1)
   if a.strip() and b.strip():out.append(Asset(a.strip(),b.strip()))
 return tuple(out)
@dataclass(frozen=True)
class Settings:
 telegram_bot_token:str=os.getenv("TELEGRAM_BOT_TOKEN","").strip()
 telegram_owner_id:int=_int("TELEGRAM_OWNER_ID",0)
 telegram_chat_id:int=_int("TELEGRAM_CHAT_ID",0)
 gemini_api_key:str=os.getenv("GEMINI_API_KEY","").strip()
 gemini_model:str=os.getenv("GEMINI_MODEL","gemini-3.6-flash").strip()
 twelve_data_api_key:str=os.getenv("TWELVE_DATA_API_KEY","").strip()
 deriv_app_id:str=os.getenv("DERIV_APP_ID","").strip()
 deriv_demo_token:str=os.getenv("DERIV_DEMO_TOKEN","").strip()
 deriv_real_token:str=os.getenv("DERIV_REAL_TOKEN","").strip()
 deriv_currency:str=os.getenv("DERIV_CURRENCY","USD").strip().upper()
 auto_trade:bool=_bool("AUTO_TRADE",False)
 enable_live_trading:bool=_bool("ENABLE_LIVE_TRADING",False)
 default_mode:str=os.getenv("DEFAULT_MODE","demo").strip().lower()
 default_expiry_minutes:int=max(1,min(60,_int("DEFAULT_EXPIRY_MINUTES",5)))
 signal_interval_seconds:int=max(60,_int("SIGNAL_INTERVAL_SECONDS",3600))
 min_confidence:int=max(50,min(99,_int("MIN_CONFIDENCE",75)))
 base_stake:float=max(.35,_float("BASE_STAKE",1.))
 max_stake:float=max(.35,_float("MAX_STAKE",5.))
 profit_target:float=max(.01,_float("PROFIT_TARGET",20.))
 max_session_loss:float=max(.01,_float("MAX_SESSION_LOSS",5.))
 session_hours:float=max(.25,_float("SESSION_HOURS",2.))
 max_trades_per_session:int=max(1,_int("MAX_TRADES_PER_SESSION",2))
 max_consecutive_losses:int=max(1,_int("MAX_CONSECUTIVE_LOSSES",2))
 martingale_max_levels:int=max(0,min(3,_int("MARTINGALE_MAX_LEVELS",3)))
 martingale_multiplier:float=max(1.,_float("MARTINGALE_MULTIPLIER",2.))
 timezone:str=os.getenv("TIMEZONE","Africa/Lagos").strip()
 assets:tuple[Asset,...]=_assets()
settings=Settings()
