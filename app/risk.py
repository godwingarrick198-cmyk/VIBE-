from __future__ import annotations
from dataclasses import dataclass,field
from datetime import datetime,timedelta,timezone
@dataclass
class RiskState:
    profit_target:float; max_session_loss:float; session_hours:float; max_trades:int; max_consecutive_losses:int
    started_at:datetime=field(default_factory=lambda:datetime.now(timezone.utc)); pnl:float=0.; trades:int=0; consecutive_losses:int=0; enabled:bool=False
    def can_trade(self)->tuple[bool,str]:
        if not self.enabled:return False,'Execution is stopped'
        if datetime.now(timezone.utc)>=self.started_at+timedelta(hours=self.session_hours):self.enabled=False;return False,'Session time limit reached'
        if self.pnl>=self.profit_target:self.enabled=False;return False,'Profit target reached'
        if self.pnl<=-abs(self.max_session_loss):self.enabled=False;return False,'Maximum session loss reached'
        if self.trades>=self.max_trades:self.enabled=False;return False,'Maximum trades for this session reached'
        if self.consecutive_losses>=self.max_consecutive_losses:self.enabled=False;return False,'Maximum consecutive losses reached'
        return True,'OK'
    def record_result(self,profit:float)->None:
        self.pnl+=float(profit);self.trades+=1;self.consecutive_losses=self.consecutive_losses+1 if profit<0 else 0
    def reset_session(self)->None:
        self.started_at=datetime.now(timezone.utc);self.pnl=0.;self.trades=0;self.consecutive_losses=0;self.enabled=True
def stake_for_level(base_stake:float,level:int,multiplier:float,max_stake:float)->float:
    if level<0:raise ValueError('level cannot be negative')
    return round(min(float(base_stake)*(float(multiplier)**int(level)),max_stake),2)
