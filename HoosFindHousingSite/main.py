from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles

app = FastAPI()


# 1. Define the nested data structures
class Basics(BaseModel):
    budget: int
    distance: float
    location: str
    bedrooms: str


class Amenities(BaseModel):
    laundry: bool
    parking: bool
    fitness: bool
    pool: bool
    ac: bool
    furniture: bool


class RoommateMatching(BaseModel):
    enabled: bool
    sleep_schedule: str
    study_habits: str
    cleanliness: str


# 2. Combine them into the final expected payload
class UserPreferences(BaseModel):
    basics: Basics
    amenities: Amenities
    roommate_matching: RoommateMatching


# 3. The API Endpoint
@app.post("/api/search")
async def search_housing(prefs: UserPreferences):

    # Print the received data to your terminal so you can see it working!
    print("--- RECEIVED NEW SEARCH REQUEST ---")
    print(f"Budget: ${prefs.basics.budget}, Beds: {prefs.basics.bedrooms}")
    print(f"Wants In-Unit Laundry: {prefs.amenities.laundry}")
    print(f"Roommate Matching Enabled: {prefs.roommate_matching.enabled}")

    # Mock Response Data
    mock_results = [
        {
            "name": "The Barringer",
            "price": "2,290",
            "distance": "0.0",
            "beds": "1 Bed",
            "amenities_matched": ["In-Unit Laundry", "AC", "Dishwasher"],
            "overall_score": 96,
            "amenity_score": 88,
            "roommate": "N/A",
        },
        {
            "name": "10th & Dairy",
            "price": "2,003",
            "distance": "0.8",
            "beds": "1 Bed",
            "amenities_matched": ["Fitness Room", "Pool", "In-Unit Laundry", "AC"],
            "overall_score": 92,
            "amenity_score": 100,
            "roommate": "David K. (98% Compatibility)",
        },
        {
            "name": "Barracks Road Apartments",
            "price": "1,503",
            "distance": "4",
            "beds": "2 Bed",
            "amenities_matched": ["Pool", "In-Unit Laundry", "AC"],
            "overall_score": 92,
            "amenity_score": 100,
            "roommate": "Tom J. (98% Compatibility)",
        },
    ]

    return {"status": "success", "results": mock_results}


# Mount the static directory
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
