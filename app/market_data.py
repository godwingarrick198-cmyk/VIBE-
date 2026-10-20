from __future__ import annotations
from datetime import datetime,timedelta,timezone
import httpx
BASE_URL="https://api.twelvedata.com/time_series"
class MarketDataError(RuntimeError):pass
class TwelveDataClient:
 def __init__(self,api_key:str):self.api_key=api_key
 async def candles(self,symbol:str,interval:str="5min",outputsize:int=120,start_date:str|None=None,end_date:str|None=None)->list[dict]:
  if not self.api_key:raise MarketDataError("TWELVE_DATA_API_KEY is not configured")
  params={"symbol":symbol,"interval":interval,"outputsize":min(max(int(outputsize),1),5000),"order":"ASC","apikey":self.api_key,"format":"JSON"}
  if start_date:params["start_date"]=start_date
  if end_date:params["end_date"]=end_date
  async with httpx.AsyncClient(timeout=30.) as client:
   response=await client.get(BASE_URL,params=params);response.raise_for_status();payload=response.json()
  if payload.get("status")=="error" or "values" not in payload:raise MarketDataError(str(payload.get("message",payload.get("code","No candle values returned"))))
  rows=[]
  for r in payload["values"]:
   try:rows.append({"datetime":r.get("datetime",""),"open":float(r["open"]),"high":float(r["high"]),"low":float(r["low"]),"close":float(r["close"]),"volume":float(r.get("volume") or 0)})
   except (KeyError,TypeError,ValueError):pass
  if len(rows)<30:raise MarketDataError(f"Only {len(rows)} usable candles returned for {symbol}")
  return rows
 async def six_month_history(self,symbol:str,months:int=6)->list[dict]:
  end=datetime.now(timezone.utc).replace(tzinfo=None,second=0,microsecond=0);start=end-timedelta(days=30*months);cursor=start;all_rows={}
  while cursor<end:
   chunk_end=min(cursor+timedelta(days=7),end)
   rows=await self.candles(symbol,"5min",2500,cursor.strftime("%Y-%m-%d %H:%M:%S"),chunk_end.strftime("%Y-%m-%d %H:%M:%S"))
   for row in rows:all_rows[row["datetime"]]=row
   cursor=chunk_end
  result=[all_rows[k] for k in sorted(all_rows)]
  if len(result)<100:raise MarketDataError("Historical request returned too few candles; check symbol, plan quota, and date support")
  return result
