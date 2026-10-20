from __future__ import annotations
import json,re
from google import genai
class AnalysisError(RuntimeError):pass
class GeminiSignalAnalyzer:
 def __init__(self,api_key:str,model:str):self.api_key,self.model=api_key,model
 async def analyze(self,symbol:str,features:dict)->dict:
  if not self.api_key:raise AnalysisError("GEMINI_API_KEY is not configured")
  prompt=f"""Analyze short-duration market direction cautiously using only these supplied candle features. Return one JSON object: direction BUY or SELL, confidence integer 0-100, rationale one short sentence. Confidence is an uncalibrated model score, not a probability. If evidence is weak, choose the better-supported direction but use a low score. Do not invent prices. Instrument: {symbol}. Data: {json.dumps(features,separators=(',',':'))}"""
  try:
   response=await genai.Client(api_key=self.api_key).aio.models.generate_content(model=self.model,contents=prompt,config={"response_mime_type":"application/json"})
   text=(response.text or "").strip();match=re.search(r"\{.*\}",text,re.DOTALL);data=json.loads(match.group(0) if match else text)
   direction=str(data.get("direction","")).upper();confidence=int(data.get("confidence",-1));rationale=str(data.get("rationale","")).strip()[:240]
   if direction not in {"BUY","SELL"} or not 0<=confidence<=100 or not rationale:raise AnalysisError("Gemini response failed validation")
   return {"direction":direction,"confidence":confidence,"rationale":rationale}
  except AnalysisError:raise
  except Exception as exc:raise AnalysisError(f"Gemini analysis failed: {exc}") from exc
