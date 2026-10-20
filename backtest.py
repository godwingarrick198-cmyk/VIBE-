from __future__ import annotations
import argparse,asyncio
from app.config import settings
from app.market_data import TwelveDataClient
def baseline_ema_backtest(candles:list[dict],payout_multiplier:float=.80)->dict:
 closes=[float(r["close"]) for r in candles]
 if len(closes)<40:raise ValueError("Need at least 40 candles")
 af,ass=2/10,2/22;fast=[closes[0]];slow=[closes[0]]
 for c in closes[1:]:
  fast.append(af*c+(1-af)*fast[-1]);slow.append(ass*c+(1-ass)*slow[-1])
 wins=losses=trades=0;net=0.
 for i in range(30,len(closes)-1):
  direction=1 if fast[i]>slow[i] else -1;move=closes[i+1]-closes[i]
  if move==0:continue
  won=(direction==1 and move>0) or (direction==-1 and move<0);trades+=1
  if won:wins+=1;net+=payout_multiplier
  else:losses+=1;net-=1.
 return {"candles":len(candles),"trades":trades,"wins":wins,"losses":losses,"win_rate_pct":round(100*wins/trades,2) if trades else 0.,"net_units":round(net,2),"assumed_win_payout_multiplier":payout_multiplier}
async def run(symbol:str,months:int):
 candles=await TwelveDataClient(settings.twelve_data_api_key).six_month_history(symbol,months=months)
 print(f"Symbol: {symbol}\nRequested period: {months} months\nFirst candle: {candles[0]['datetime']}\nLast candle: {candles[-1]['datetime']}")
 for k,v in baseline_ema_backtest(candles).items():print(f"{k}: {v}")
 print("WARNING: illustrative EMA baseline only; not Gemini strategy or a forecast.")
if __name__=="__main__":
 p=argparse.ArgumentParser(description="Historical candles and illustrative EMA baseline")
 p.add_argument("--symbol",default="EUR/USD");p.add_argument("--months",type=int,default=6);a=p.parse_args();asyncio.run(run(a.symbol,max(1,min(12,a.months))))
