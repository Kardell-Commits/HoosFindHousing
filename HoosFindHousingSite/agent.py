import math
from models import UserPreferences, Listing, Score

# These weights can be changed, but they must add up to 1.0
WEIGHTS = {
    "rent":     0.35,
    "distance": 0.30,
    "amenity":  0.25,
    "bedroom":  0.10,
}

# Each entry: (UserPreferences attribute path, csv column, friendly label)
AMENITY_PREF_MAP: list[tuple[str, str, str]] = [
    ("laundry",    "washer/dryer in unit", "In-Unit Laundry"),
    ("parking",    "parking",              "Parking"),
    ("fitness",    "gym",                  "Fitness Room"),
    ("pool",       "pool",                 "Pool"),
    ("ac",         "dishwasher",           "AC"),      # AC not in CSV; proxy via dishwasher column
    ("furniture",  "furnished",            "Furnished"),
]
# Note: "ac" (air conditioning) is not a dedicated boolean column in the CSV.
# We detect it from the free-text amenities string instead (see score_amenities).

# Scores how well the rent is compared to the student's budget
def score_rent(listing: dict, prefs: UserPreferences) -> float:

    # Return neutral score of 50 if you must call for rent
    if listing.get("call for rent", 0) == 1:
        return 50.0

    # Get the price, return 50 if it is unknown
    price = listing.get("price_avg")
    if price is None or math.isnan(price):
        return 50.0

    budget = prefs.basics.budget
    if budget <= 0:
        return 50.0

    # 1.0 = exactly at budget
    ratio = price / budget

    # Decreases score more and more as it goes over the budget, score is 0 if rent is above 125%
    if ratio <= 1.0:
        return 100.0
    elif ratio <= 1.10:

        return 100.0 - (ratio - 1.0) / 0.10 * 50.0

    elif ratio <= 1.25:

        return 50.0 - (ratio - 1.10) / 0.15 * 50.0

    else:
        return 0.0

# Scores how close the listing is to grounds
def score_distance(listing: dict, prefs: UserPreferences) -> float:

    # Small penalty for not having data related to distance
    dist = listing.get("distance")
    if dist is None or math.isnan(dist):
        return 40.0

    # Default value of 10 is max distance is not provided
    max_dist = prefs.basics.distance
    if max_dist <= 0:
        max_dist = 10.0

    # Disqualified if greater than max distance
    if dist > max_dist:
        return 0.0

    # Perfect score for distance of 0, score gets smaller as listing gets farther away
    score = 100.0 * (1.0 - dist / max_dist) ** 1.5
    return max(0.0, min(100.0, score))

# Creates the score based on how many amenities the listing has, but only if the amenity is something the student wants
def score_amenities(listing: dict, prefs: UserPreferences) -> tuple[float, list[str]]:

    amenities_text = str(listing.get("amenities", "")).lower()

    desired_count = 0
    matched_count = 0
    matched_labels: list[str] = []

    # In unit laundry is desired, but on-site laundry is OK as well
    if prefs.amenities.laundry:
        desired_count += 1
        if listing.get("washer/dryer in unit", 0) == 1:
            matched_count += 1
            matched_labels.append("In-Unit Laundry")
        elif listing.get("laundry available", 0) == 1:
            # Partial credit (0.6) for on-site laundry
            matched_count += 0.6
            matched_labels.append("Laundry On-Site")

    # Parking
    if prefs.amenities.parking:
        desired_count += 1
        if listing.get("parking", 0) == 1:
            matched_count += 1
            matched_labels.append("Parking")

    # Fitness room / gym
    if prefs.amenities.fitness:
        desired_count += 1
        if listing.get("gym", 0) == 1:
            matched_count += 1
            matched_labels.append("Fitness Room")

    # Pool
    if prefs.amenities.pool:
        desired_count += 1
        if listing.get("pool", 0) == 1:
            matched_count += 1
            matched_labels.append("Pool")

    # AC — check free-text column (no dedicated boolean)
    if prefs.amenities.ac:
        desired_count += 1
        if "air conditioning" in amenities_text or "central air" in amenities_text:
            matched_count += 1
            matched_labels.append("AC")

    # Furnished
    if prefs.amenities.furniture:
        desired_count += 1
        if listing.get("furnished", 0) == 1:
            matched_count += 1
            matched_labels.append("Furnished")

    # Calculates score based on the ratio of matched amenities to desired amenities
    if desired_count == 0:
        amenity_score = 100.0
    else:
        amenity_score = 100.0 * matched_count / desired_count

    return amenity_score, matched_labels

# Score based on how many desired bedrooms there are
def score_bedrooms(listing: dict, prefs: UserPreferences) -> float:

    pref_beds_str = prefs.basics.bedrooms.strip().lower()

    # Automatically returns 100 if there is no preference for bedrooms
    if pref_beds_str == "any":
        return 100.0

    listing_beds = listing.get("beds")
    if listing_beds is None or math.isnan(listing_beds):
        return 50.0

    listing_beds = int(listing_beds)

    if pref_beds_str == "4+":
        return 100.0 if listing_beds >= 4 else max(0.0, 100.0 - (4 - listing_beds) * 40.0)

    # Returns neutral value if number of beds is not recognized
    try:
        pref_beds = int(pref_beds_str)
    except ValueError:
        return 50.0

    diff = abs(listing_beds - pref_beds)
    if diff == 0:
        return 100.0
    elif diff == 1:
        return 60.0
    else:
        return max(0.0, 20.0 - (diff - 2) * 10.0)

# Computes the overall score for an individual listing, and also returns the score breakdown
def score_listing(listing: dict, prefs: UserPreferences) -> tuple[float, Score, list[str]]:

    rent_score = score_rent(listing, prefs)
    distance_score = score_distance(listing, prefs)
    amenity_score, matched_labels = score_amenities(listing, prefs)
    bedroom_score = score_bedrooms(listing, prefs)

    overall = (
            WEIGHTS["rent"] * rent_score +
            WEIGHTS["distance"] * distance_score +
            WEIGHTS["amenity"] * amenity_score +
            WEIGHTS["bedroom"] * bedroom_score
    )
    overall = round(min(100.0, max(0.0, overall)), 1)

    breakdown = Score(
        rent_score=round(rent_score, 1),
        distance_score=round(distance_score, 1),
        amenities_score=round(amenity_score, 1),
        bedroom_score=round(bedroom_score, 1),
    )

    return overall, breakdown, matched_labels

# Scores every listing in the data and ranks them
def rank_listings(
        listings: list[dict],
        prefs: UserPreferences,
        top_n: int = 20,
) -> list[Listing]:

    scored: list[tuple[float, dict, Score, list[str]]] = []

    for listing in listings:
        overall, breakdown, matched_labels = score_listing(listing, prefs)
        scored.append((overall, listing, breakdown, matched_labels))

    scored.sort(key=lambda x: x[0], reverse=True)

    results: list[Listing] = []
    for overall, listing, breakdown, matched_labels in scored[:top_n]:
        # Build a clean price display string
        price_avg = listing.get("price_avg")
        if listing.get("call for rent", 0) == 1:
            price_display = "Call for Rent"
        elif price_avg is not None and not math.isnan(price_avg):
            price_display = f"${price_avg:,.0f}"
        else:
            price_display = listing.get("price", "N/A")

        dist = listing.get("distance")

        results.append(Listing(
            name=listing.get("title") or "Unknown Property",
            address=listing.get("address"),
            link=listing.get("link", ""),
            price=price_display,
            price_avg=price_avg if (price_avg and not math.isnan(price_avg)) else None,
            distance=dist if (dist is not None and not math.isnan(dist)) else None,
            bedrooms=listing.get("beds") if not (listing.get("beds") is None) else None,
            bathrooms=listing.get("baths"),
            sqft=str(listing.get("sqft", "")) or None,
            availability=listing.get("availability"),
            amenities=matched_labels,
            overall_score=overall,
            score_breakdown=breakdown,
            call_for_rent=bool(listing.get("call for rent", 0)),
        ))

    return results