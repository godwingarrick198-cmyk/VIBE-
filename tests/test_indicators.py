from app.indicators import ema,rsi,candle_features
from app.risk import RiskState,stake_for_level
def test_ema_length_and_direction():
 r=ema([1.,2.,3.,4.],2);assert len(r)==4 and r[-1]>r[0]
def test_rsi_uptrend():assert rsi([float(i) for i in range(1,20)],14)==100.
def test_features_need_enough_candles():
 c=[{"open":i,"high":i+1,"low":i-1,"close":i} for i in range(1,40)]
 f=candle_features(c);assert f["candle_count"]==39 and f["ema_9"]>f["ema_21"]
def test_stake_is_capped():assert stake_for_level(1,3,2,5)==5
def test_risk_stops_after_target():
 s=RiskState(10,5,2,5,2);s.enabled=True;s.record_result(10);assert not s.can_trade()[0]
