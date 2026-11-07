#!/usr/bin/env python3
import json, math, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo
import requests

ROOT=Path(__file__).resolve().parents[1]
CONFIG=json.loads((ROOT/"data/instruments.json").read_text())
OUT=ROOT/"market-data.json"
IST=ZoneInfo("Asia/Kolkata")
BASE="https://query1.finance.yahoo.com/v8/finance/chart/"
HEADERS={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36","Accept":"application/json"}

def previous_data():
    try: return json.loads(OUT.read_text())
    except Exception: return {"quotes":{}}

def fetch(session,symbol):
    last_error="unknown error"
    for attempt in range(4):
        try:
            r=session.get(BASE+quote(symbol,safe=""),params={"range":"5d","interval":"1d","events":"div,splits"},headers=HEADERS,timeout=25)
            if r.status_code==429 or r.status_code>=500: raise RuntimeError("HTTP "+str(r.status_code))
            r.raise_for_status()
            root=r.json().get("chart",{})
            if root.get("error"): raise RuntimeError(str(root["error"]))
            result=(root.get("result") or [None])[0]
            if not result: raise RuntimeError("No chart result")
            meta=result.get("meta") or {}
            if str(meta.get("symbol","")).upper()!=symbol.upper(): raise RuntimeError("Ticker mismatch")
            if str(meta.get("currency","")).upper()!="INR": raise RuntimeError("Unexpected/missing currency")
            ts=result.get("timestamp") or []
            closes=((result.get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
            bars=[(int(t),float(c)) for t,c in zip(ts,closes) if t is not None and c is not None and math.isfinite(float(c)) and float(c)>0]
            if not bars: raise RuntimeError("No valid daily close")
            stamp,price=bars[-1]
            dt=datetime.fromtimestamp(stamp,timezone.utc).astimezone(IST)
            if dt.date()>datetime.now(IST).date(): raise RuntimeError("Future-dated close")
            return {"price":round(price,4),"priceDate":dt.strftime("%Y-%m-%d"),"priceTimestamp":dt.isoformat(),"currency":"INR","exchange":meta.get("fullExchangeName") or meta.get("exchangeName"),"providerSymbol":meta["symbol"],"source":"Yahoo Finance chart endpoint","status":"fresh"}
        except Exception as e:
            last_error=str(e)
            if attempt<3: time.sleep(3*(2**attempt))
    raise RuntimeError(last_error)

def main():
    now=datetime.now(IST); old=previous_data().get("quotes",{}); quotes={}
    universe=list(CONFIG["instruments"])+[dict(CONFIG["benchmark"],kind="benchmark")]
    for item in universe:
        key=item["nse_symbol"]; ticker=item["yahoo_symbol"]; prior=old.get(key,{})
        try:
            q=fetch(requests.Session(),ticker)
            age=(now.date()-datetime.strptime(q["priceDate"],"%Y-%m-%d").date()).days
            q.update({"name":item["name"],"nseSymbol":key,"yahooSymbol":ticker,"kind":item.get("kind","instrument"),"updatedAt":now.isoformat(),"ageCalendarDays":age})
            if age>4: q.update(status="stale",warning="Last close is over 4 calendar days old; check market holidays or feed delay.")
        except Exception as e:
            if prior.get("price") and prior.get("priceDate"):
                q=dict(prior); age=(now.date()-datetime.strptime(q["priceDate"],"%Y-%m-%d").date()).days
                q.update(name=item["name"],nseSymbol=key,yahooSymbol=ticker,kind=item.get("kind","instrument"),status="stale",updatedAt=now.isoformat(),ageCalendarDays=age,warning="Refresh failed; showing last successful close. "+str(e))
            else:
                q={"name":item["name"],"nseSymbol":key,"yahooSymbol":ticker,"kind":item.get("kind","instrument"),"price":None,"priceDate":None,"updatedAt":now.isoformat(),"status":"unavailable","source":"Yahoo Finance chart endpoint","warning":str(e)}
        quotes[key]=q
        time.sleep(0.8)
    counts={k:sum(1 for q in quotes.values() if q.get("status")==k) for k in ("fresh","stale","unavailable")}
    data={"schemaVersion":1,"provider":"Yahoo Finance chart endpoint (unofficial/free; no API key)","generatedAt":now.isoformat(),"schedule":"Weekdays 15:50 Asia/Kolkata, after NSE close","counts":{"total":len(quotes),**counts},"disclaimer":"Indicative end-of-day closes, not exchange-certified live quotes. Yahoo data is unofficial and may be delayed, incomplete or unavailable. Stale values are not current quotes.","quotes":quotes}
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(data["counts"]))
    if counts["fresh"]<max(5,int(len(quotes)*0.25)): raise SystemExit("Too few fresh quotes; refusing to publish mostly broken data.")

if __name__=="__main__": main()
