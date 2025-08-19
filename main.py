#Paket tanımlamaları
from typing import Any, Dict, Optional
import os, json, asyncio
import httpx
from mcp.server.fastmcp import FastMCP

#API tanımlamaları
API_KEY = os.getenv("THESPORTSDB_API_KEY", "123")
USER_AGENT = os.getenv("USER_AGENT", "SportsDB-MCP-Server/1.0")
BASE_URL = "https://www.thesportsdb.com/api/v1/json"

#MCP istemcisi
mcp = FastMCP("sportsdb-v1-min")


#Yardımcı Fonksiyonlar
def _make_url(endpoint: str) -> str:
    """API endpoint'i için tam URL oluşturur"""
    return f"{BASE_URL}/{API_KEY}/{endpoint.lstrip('/')}"

async def _get(endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: float = 20.0) -> Any:
    """HTTP GET isteği gönderir ve JSON yanıtı döndürür"""
    url = _make_url(endpoint)
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers={"User-Agent": USER_AGENT}) as client:
        try:
            r = await client.get(url, headers=headers, params=params or {})
            r.raise_for_status()  

            return r.json() if "json" in r.headers.get("content-type","").lower() else {"text": r.text}
        except httpx.HTTPStatusError as e:
            body = (lambda: (e.response.json() if "json" in e.response.headers.get("content-type","").lower() else e.response.text))()
            return {"error":"HTTP","status":e.response.status_code,"url":str(e.request.url),"body":body}
        except httpx.RequestError as e:
            return {"error":"Network","message":str(e)}

def _is_err(x: Any) -> bool:
    """Yanıtın hata içerip içermediğini kontrol eder"""
    return isinstance(x, dict) and x.get("error") is not None

def _fmt_err(d: Dict[str, Any]) -> str:
    """Hata mesajını güzel bir formatta döndürür"""
    parts = [f"TheSportsDB error: {d.get('error')}"]
    if d.get("status"): parts.append(f"Status: {d['status']}")
    if d.get("url"): parts.append(f"URL: {d['url']}")
    if d.get("message"): parts.append(f"Message: {d['message']}")
    b = d.get("body")
    if b is not None:
        parts.append("Body: " + (json.dumps(b, ensure_ascii=False) if isinstance(b, (dict, list)) else str(b))[:800])
    return "\n".join(parts)

def _pretty(obj: Any, max_len: int = 1200) -> str:
    """JSON formatında döndürüyor"""
    try: 
        s = json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception: 
        s = str(obj)
    return s if len(s) <= max_len else s[:max_len] + " ..."

#Agentın kullanacağı MPC toolları
@mcp.tool()
async def search_teams(name: str, limit: int = 10) -> str:
    """Takımı araması yapıyor"""
    j = await _get("searchteams.php", {"t": name})
    if _is_err(j): return _fmt_err(j) 

    teams = (j or {}).get("teams") or []
    if not teams: return "No teams found."

    lines = [f"Found {len(teams)} teams (showing up to {limit}):"]
    for t in teams[:limit]:
        lines.append(f"- {t.get('strTeam')} | League: {t.get('strLeague')} | Sport: {t.get('strSport')} | ID: {t.get('idTeam')}")
    return "\n".join(lines)

@mcp.tool()
async def list_players(team_id: int) -> str:
    """Takımın belirli oyuncularını döndürüyor"""
    j = await _get("lookup_all_players.php", {"id": int(team_id)})
    if _is_err(j): return _fmt_err(j)
    
    players = (j or {}).get("player") or []
    if not players: return "No players found."
    
    lines = [f"Found {len(players)} players:"]
    for p in players:
        lines.append(f"- {p.get('strPlayer')} | Pos: {p.get('strPosition')} | Nationality: {p.get('strNationality')} | ID: {p.get('idPlayer')}")
    return "\n".join(lines)

@mcp.tool()
async def team_next(team_id: int, limit: int = 10) -> str:
    """Gelecek maçları gösteriyor"""
    j = await _get("eventsnext.php", {"id": int(team_id)})
    if _is_err(j): return _fmt_err(j)
    
    evs = (j or {}).get("events") or []  
    if not evs: return "No upcoming events."
    
    lines = [f"Next {min(limit, len(evs))} events:"]
    for e in evs[:limit]:
        lines.append(f"- {e.get('strEvent')} | {e.get('dateEvent')} {e.get('strTime')} | ID: {e.get('idEvent')}")
    return "\n".join(lines)

@mcp.tool()
async def team_last(team_id: int, limit: int = 10) -> str:
    """Geçmiş maçları gösteriyor"""
    j = await _get("eventslast.php", {"id": int(team_id)})
    if _is_err(j): return _fmt_err(j)
    
    evs = (j or {}).get("results") or (j or {}).get("events") or []
    if not evs: return "No past events."
    
    lines = [f"Last {min(limit, len(evs))} events:"]
    for e in evs[:limit]:
        lines.append(f"- {e.get('strEvent')} | {e.get('dateEvent')} {e.get('strTime')} | ID: {e.get('idEvent')} | Score: {e.get('intHomeScore')}-{e.get('intAwayScore')}")
    return "\n".join(lines)

@mcp.tool()
async def list_leagues(country: str, sport: str) -> str:
    """Ligleri listeliyor"""
    j = await _get("search_all_leagues.php", {"c": country, "s": sport})
    return _pretty(j)  


@mcp.tool()
async def event_full(event_id: int) -> dict:
    """Bir maçın tüm detaylarını getirir"""
    t1 = _get("lookupevent.php", {"id": int(event_id)})       
    t2 = _get("lookuplineup.php", {"id": int(event_id)})      
    t3 = _get("lookuptimeline.php", {"id": int(event_id)})     
    t4 = _get("lookupeventstats.php", {"id": int(event_id)})   
    t5 = _get("lookuptv.php", {"id": int(event_id)})          
    
    ev, lineup, timeline, stats, tv = await asyncio.gather(t1, t2, t3, t4, t5)
    
    return {"event": ev, "lineup": lineup, "timeline": timeline, "stats": stats, "tv": tv}

@mcp.tool()
async def raw_get(endpoint: str = "searchteams.php", query_json: str = "") -> dict:
    """Raw api isteği yapıyor"""
    try:
        params = json.loads(query_json) if query_json else {}
        if not isinstance(params, dict): params = {}
    except Exception:
        params = {}
    return await _get(endpoint, params)

if __name__ == "__main__":
    mcp.run(transport="stdio")
