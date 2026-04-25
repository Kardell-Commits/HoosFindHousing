from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import json
import os
from openai import OpenAI
from models import UserPreferences, Listing, RefineRequest
from data import LISTINGS
from agent import rank_listings
from dotenv import load_dotenv
load_dotenv()

client= OpenAI(api_key=os.getenv("OPENAI_KEY"))
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
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))

    return {
        "status": "success",
        "total_listings_scored": len(LISTINGS),
        "results": [r.model_dump() for r in results],
    }

@app.post("/api/refine", response_model=dict)
async def refine_housing(request: RefineRequest):
    try:
        if not os.getenv("OPENAI_KEY"):
            raise HTTPException(
                status_code=500, detail="OPENAI KEY IS MISSING."
            )
        system_instructions=f"""
You are a housing search configuration assistant for UVA students.

Update the user's housing preferences based on their natural language request.

Return ONLY valid JSON.
Do not include markdown.
Do not include explanations.
Do not include conversational text.

The JSON must match this exact same structure:
{request.current_prefs.model_dump_json()}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": request.prompt},
            ],
            response_format={"type": "json_object"},
        )

        updated_prefs_dict = json.loads(response.choices[0].message.content)

        updated_prefs = UserPreferences(**updated_prefs_dict)

        results = rank_listings(LISTINGS, updated_prefs, top_n=20)

        return {
            "status": "success",
            "updated_prefs": updated_prefs.model_dump(),
            "results": [r.model_dump() for r in results],
        }

    except HTTPException:
        raise

    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/health")
async def health():
    return {"status": "ok", "listings_loaded": len(LISTINGS)}

# Mount the static directory
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
