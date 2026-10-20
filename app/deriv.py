from __future__ import annotations
import json,websockets
class DerivAPIError(RuntimeError):pass
class DerivClient:
 def __init__(self,app_id:str,token:str):self.app_id,self.token=app_id,token
 @property
 def endpoint(self):
  if not self.app_id:raise DerivAPIError("DERIV_APP_ID is not configured")
  return f"wss://ws.derivws.com/websockets/v3?app_id={self.app_id}"
 async def call(self,payload:dict,authenticated:bool=True)->dict:
  if authenticated and not self.token:raise DerivAPIError("Deriv token missing for selected mode")
  try:
   async with websockets.connect(self.endpoint,open_timeout=20,close_timeout=5,ping_interval=20) as ws:
    if authenticated:
     await ws.send(json.dumps({"authorize":self.token}));auth=json.loads(await ws.recv())
     if auth.get("error"):raise DerivAPIError(auth["error"].get("message","Authorization failed"))
    await ws.send(json.dumps(payload));response=json.loads(await ws.recv())
    if response.get("error"):raise DerivAPIError(response["error"].get("message","Deriv request failed"))
    return response
  except DerivAPIError:raise
  except Exception as exc:raise DerivAPIError(f"Deriv connection/request failed: {exc}") from exc
 async def balance(self):return (await self.call({"balance":1})).get("balance",{})
 async def active_symbols(self):return (await self.call({"active_symbols":"brief","product_type":"basic"},authenticated=False)).get("active_symbols",[])
 async def buy_direction(self,symbol:str,direction:str,stake:float,expiry_minutes:int,currency:str)->dict:
  if direction not in {"BUY","SELL"}:raise DerivAPIError("Direction must be BUY or SELL")
  quote=await self.call({"proposal":1,"amount":round(float(stake),2),"basis":"stake","contract_type":"CALL" if direction=="BUY" else "PUT","currency":currency,"duration":int(expiry_minutes)*60,"duration_unit":"s","underlying_symbol":symbol})
  proposal=quote.get("proposal")
  if not proposal or not proposal.get("id"):raise DerivAPIError("No valid proposal; symbol/contract may be unsupported")
  bought=await self.call({"buy":proposal["id"],"price":float(proposal.get("ask_price",stake))});contract=bought.get("buy",{})
  if not contract.get("contract_id"):raise DerivAPIError("Deriv did not return contract ID")
  return {"contract_id":int(contract["contract_id"]),"buy_price":float(contract.get("buy_price",stake)),"payout":float(contract.get("payout",0)),"longcode":contract.get("longcode",""),"contract_type":"CALL" if direction=="BUY" else "PUT","symbol":symbol}
 async def contract_status(self,contract_id:int)->dict:
  return (await self.call({"proposal_open_contract":1,"contract_id":int(contract_id)})).get("proposal_open_contract",{})
