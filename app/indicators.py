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


def historical_features(candles: list[dict]) -> dict:
    """Compact six-month hourly-history summary for AI context."""
    from datetime import datetime
    closes=[]
    dated=[]
    for row in candles:
        try:
            close=float(row["close"])
            stamp=datetime.fromisoformat(str(row["datetime"]))
            if isfinite(close) and close>0:
                closes.append(close); dated.append((stamp,close))
        except (KeyError,TypeError,ValueError):
            continue
    if len(closes)<100:
        raise ValueError("At least 100 valid historical hourly candles are required")
    fast,slow=ema(closes,20),ema(closes,50)
    returns=[(closes[i]-closes[i-1])/closes[i-1]*100 for i in range(1,len(closes)) if closes[i-1]]
    peak=closes[0];max_drawdown=0.0
    for close in closes:
        peak=max(peak,close)
        if peak: max_drawdown=min(max_drawdown,(close-peak)/peak*100)
    monthly={}
    for stamp,close in dated:
        key=stamp.strftime("%Y-%m")
        if key not in monthly: monthly[key]=[close,close]
        monthly[key][1]=close
    monthly_returns={key:round((values[1]/values[0]-1)*100,3) for key,values in monthly.items() if values[0]}
    same_direction=0;comparable=0
    for i in range(1,len(returns)):
        if returns[i] and returns[i-1]:
            comparable+=1
            if (returns[i]>0)==(returns[i-1]>0):same_direction+=1
    return {
        "timeframe":"1h",
        "historical_candles":len(closes),
        "history_start":dated[0][0].isoformat(),
        "history_end":dated[-1][0].isoformat(),
        "history_days":(dated[-1][0]-dated[0][0]).days,
        "six_month_return_pct":round((closes[-1]/closes[0]-1)*100,3),
        "ema_20":round(fast[-1],6),
        "ema_50":round(slow[-1],6),
        "ema_spread_pct":round((fast[-1]-slow[-1])/closes[-1]*100,4),
        "rsi_14":round(rsi(closes,14),3) if rsi(closes,14) is not None else None,
        "average_absolute_hourly_change_pct":round(sum(abs(x) for x in returns)/len(returns),5) if returns else 0,
        "maximum_peak_to_trough_drawdown_pct":round(max_drawdown,3),
        "same_direction_consecutive_hour_pct":round(same_direction/comparable*100,2) if comparable else None,
        "monthly_returns_pct":monthly_returns,
    }
