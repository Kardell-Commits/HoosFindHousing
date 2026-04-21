from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from models import UserPreferences, Listing
from data import LISTINGS
from agent import rank_listings
app = FastAPI(title="Hoos Find Housing", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. The API Endpoint
@app.post("/api/search", response_model=dict)
async def search_housing(prefs: UserPreferences):

    # Accepts user preferences, scores them, and lists them
    try:
        results: list[Listing] = rank_listings(LISTINGS, prefs, top_n=20)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "status": "success",
        "total_listings_scored": len(LISTINGS),
        "results": [r.model_dump() for r in results],
    }

@app.get("/api/health")
async def health():
    return {"status": "ok", "listings_loaded": len(LISTINGS)}

# Mount the static directory
#app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
