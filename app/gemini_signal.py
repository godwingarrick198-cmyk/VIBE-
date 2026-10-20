from __future__ import annotations
import asyncio,json,re
from google import genai

class AnalysisError(RuntimeError):pass

class GeminiSignalAnalyzer:
 def __init__(self,api_key:str,model:str):
  self.api_key,self.model=api_key,model
  self.client=genai.Client(api_key=api_key) if api_key else None

 async def analyze(self,symbol:str,features:dict)->dict:
  if not self.api_key or self.client is None:
   raise AnalysisError("GEMINI_API_KEY is not configured")
  prompt=f"""Analyze short-duration market direction cautiously using only these supplied candle features. Return one JSON object: direction BUY or SELL, confidence integer 0-100, rationale one short sentence. Confidence is an uncalibrated model score, not a probability. If evidence is weak, choose the better-supported direction but use a low score. Do not invent prices. Instrument: {symbol}. Data: {json.dumps(features,separators=(',',':'))}"""
  try:
   # Gemini 4 uses the Interactions API. Run its synchronous SDK call in a
   # worker thread so it does not block the Telegram/market-data event loop.
   response=await asyncio.to_thread(
    self.client.interactions.create,
    model=self.model,
    input=prompt,
    generation_config={"thinking_level":"medium"}
   )
   text=(getattr(response,"output_text","") or "").strip()
   match=re.search(r"\{.*\}",text,re.DOTALL)
   data=json.loads(match.group(0) if match else text)
   direction=str(data.get("direction","")).upper()
   confidence=int(data.get("confidence",-1))
   rationale=str(data.get("rationale","")).strip()[:240]
   if direction not in {"BUY","SELL"} or not 0<=confidence<=100 or not rationale:
    raise AnalysisError("Gemini response failed validation")
   return {"direction":direction,"confidence":confidence,"rationale":rationale}
  except AnalysisError:
   raise
  except Exception as exc:
   raise AnalysisError(f"Gemini analysis failed: {exc}") from exc
