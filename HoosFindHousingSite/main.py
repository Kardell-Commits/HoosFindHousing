from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import json
import ollama
from models import UserPreferences, Listing, RefineRequest
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
        # 1. Provide instructions and current state to the local LLM
        system_instructions = f"""
        You are a housing search configuration assistant for UVA students. 
        Update the JSON values based on the text request. 
        Return ONLY valid JSON matching the exact same structure. Do not return conversational text.
        Current Preferences:
        {request.current_prefs.model_dump_json()}
        """

        # 2. Call local Ollama model
        response = ollama.chat(
            model='llama3.2:1b',
            messages=[
                {'role': 'system', 'content': system_instructions},
                {'role': 'user', 'content': request.prompt}
            ],
            format='json',
            options={'keep_alive': '1h'}
        )
        
        # 3. Parse response and update your Pydantic model
        updated_prefs_dict = json.loads(response['message']['content'])
        updated_prefs = UserPreferences(**updated_prefs_dict)
        
        # 4. Feed the AI-updated preferences back into the algorithm
        results = rank_listings(LISTINGS, updated_prefs, top_n=20)
        
        return {
            "status": "success",
            "updated_prefs": updated_prefs.model_dump(), 
            "results": [r.model_dump() for r in results],
        }
    except Exception as exc:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/health")
async def health():
    return {"status": "ok", "listings_loaded": len(LISTINGS)}

# Mount the static directory
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
