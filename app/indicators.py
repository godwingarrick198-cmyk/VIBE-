from __future__ import annotations
from math import isfinite

def ema(values: list[float], period: int) -> list[float]:
    if period < 1: raise ValueError('period must be >= 1')
    if not values: return []
    alpha=2.0/(period+1); out=[float(values[0])]
    for value in values[1:]: out.append(alpha*float(value)+(1-alpha)*out[-1])
    return out

def rsi(values: list[float], period: int=14) -> float | None:
    if len(values)<=period: return None
    changes=[values[i]-values[i-1] for i in range(1,len(values))][-period:]
    gains=sum(max(x,0) for x in changes)/period; losses=sum(max(-x,0) for x in changes)/period
    if losses==0: return 100.0 if gains else 50.0
    return 100-(100/(1+gains/losses))

def candle_features(candles: list[dict]) -> dict:
    closes=[]
    for c in candles:
        try:
            v=float(c['close'])
            if isfinite(v): closes.append(v)
        except (KeyError,TypeError,ValueError): pass
    if len(closes)<30: raise ValueError('At least 30 valid candles are required')
    f,s=ema(closes,9),ema(closes,21); last,prev=closes[-1],closes[-2]
    return {'candle_count':len(closes),'last_close':last,'previous_close':prev,'change_pct':((last-prev)/prev*100) if prev else 0,'ema_9':f[-1],'ema_21':s[-1],'ema_spread_pct':((f[-1]-s[-1])/last*100) if last else 0,'rsi_14':rsi(closes,14),'last_candles':[{'datetime':str(c.get('datetime','')),'open':float(c['open']),'high':float(c['high']),'low':float(c['low']),'close':float(c['close'])} for c in candles[-10:] if all(k in c for k in ('open','high','low','close'))]}
