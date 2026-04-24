from pydantic import BaseModel, field_validator
from typing import Optional

# Input Models

class Basics(BaseModel):
    budget: int
    walk_time: float
    location: str = "any"
    bedrooms: str
    priority_ranking: list[str] = ["rent", "distance", "amenities", "bedrooms"]

    @field_validator('bedrooms', mode='before')
    @classmethod
    def coerce_bedrooms(cls, v):
        return str(v)

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
  
class UserPreferences(BaseModel):
    basics: Basics
    amenities: Amenities
    roommate_matching: RoommateMatching

# Output Models

class Score(BaseModel):
    rent_score: float
    distance_score: float
    amenities_score: float
    bedroom_score: float

class Listing(BaseModel):
    name: str
    address: Optional[str]
    link: str
    price: str
    price_avg: Optional[float]
    walk_minutes: Optional[float]
    drive_minutes: Optional[float]
    bedrooms: Optional[float]
    bathrooms: Optional[float]
    sqft: Optional[float]
    availability: Optional[str]
    amenities: list[str]
    overall_score: float
    score_breakdown: Score
    call_for_rent: bool

class RefineRequest(BaseModel):
    prompt: str
    current_prefs: UserPreferences