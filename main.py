import asyncio
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

INSTANCES = [
    "https://invidious.lunivers.trade",
    "https://invidious.ritoge.com",
    "https://yt.omada.cafe",
    "https://inv.nadeko.net",
    "https://inv1.nadeko.net",
    "https://inv2.nadeko.net",
    "https://inv3.nadeko.net",
    "https://inv4.nadeko.net",
    "https://inv5.nadeko.net",
    "https://inv6.nadeko.net",
    "https://inv7.nadeko.net",
    "https://inv8.nadeko.net",
    "https://inv9.nadeko.net",
    "https://invidious.f5.si",
    "https://yewtu.be",
    "https://y.com.sb",
    "https://yt.vern.cc",
    "https://inv.vern.cc",
    "https://invidious.darkness.services",
    "https://invidious.privacyredirect.com",
    "https://invidious.tiekoetter.com",
    "https://invidious.protokolla.fi",
    "https://invidious.fdn.fr",
    "https://yt.artemislena.eu",
    "https://invidious.flokinet.to",
    "https://invidious.sethforprivacy.com",
    "https://invidious.nerdvpn.de",
    "https://invidious.lunar.icu",
    "https://iv.ggtyler.dev",
    "https://nyc1.iv.ggtyler.dev",
    "https://lekker.gay",
    "https://rust.oskamp.nl",
    "https://yt.thechangebook.org",
    "https://app.materialio.us",
    "https://inv.kamuridesu.com",
    "https://invidious.projektegfau.lt",
    "https://invidious.nietzospannend.nl",
]

ERROR_KEYWORDS = ["shutdown", "blocked", "Forbidden", "<!DOCTYPE", "<html", "Rate limit", "temporarily unavailable", "maintenance"]

async def fetch_instance(client: httpx.AsyncClient, instance: str, video_id: str) -> dict | None:
    try:
        url = f"{instance}/api/v1/videos/{video_id}?hl=ja"
        r = await client.get(url, timeout=4.0)
        if r.status_code != 200:
            return None
        text = r.text
        if any(kw.lower() in text.lower() for kw in ERROR_KEYWORDS):
            return None
        data = r.json()
        if not data.get("title"):
            return None
        return data
    except Exception:
        return None

async def race_instances(video_id: str) -> dict | None:
    async with httpx.AsyncClient() as client:
        tasks = [
            asyncio.create_task(fetch_instance(client, inst, video_id))
            for inst in INSTANCES
        ]
        try:
            for coro in asyncio.as_completed(tasks):
                result = await coro
                if result is not None:
                    for t in tasks:
                        t.cancel()
                    return result
        except asyncio.CancelledError:
            pass
        return None

@app.get("/")
def root():
    return {"status": "ok", "instances": len(INSTANCES)}

@app.get("/api/v1/videos/{video_id}")
async def get_video(video_id: str):
    data = await race_instances(video_id)
    if data is None:
        raise HTTPException(status_code=503, detail="All instances failed")
    return data
