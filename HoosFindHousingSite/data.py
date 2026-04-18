import pandas as pd
import numpy as np
from pathlib import Path

CSV_PATH = Path(__file__).parent / "UVA_housing_clean.csv"

# Amenity column name → frontend-friendly label
AMENITY_COLUMNS: dict[str, str] = {
    "dishwasher":           "Dishwasher",
    "washer/dryer in unit": "In-Unit Laundry",
    "has balcony":          "Balcony",
    "gym":                  "Fitness Room",
    "internet":             "Internet Included",
    "pool":                 "Pool",
    "near bus stop":        "Near Bus Stop",
    "furnished":            "Furnished",
    "parking":              "Parking",
    "laundry available":    "Laundry On-Site",
    "pet friendly":         "Pet Friendly",
    "individual lease":     "Individual Lease",
    "disability access":    "Disability Access",
}


def load_listings() -> list[dict]:
    # Reads the csv file, cleans the data, and turns it into a list of dictionaries
    df = pd.read_csv(CSV_PATH)

    # Gets the prices, skip rows with no price
    df["price_avg"] = pd.to_numeric(df["price_avg"], errors="coerce")

    # Caps outliers with high distances
    df.loc[df["distance"] > 50, "distance"] = np.nan

    # Gets number of beds as float
    df["beds"] = pd.to_numeric(df["beds"], errors="coerce")

    # Creates a list of labels for each amenity
    def amenity_labels(row: pd.Series) -> list[str]:
        return [label for col, label in AMENITY_COLUMNS.items() if row.get(col, 0) == 1]

    df["amenity_labels"] = df.apply(amenity_labels, axis=1)

    # Convert to list-of-dicts for fast iteration
    records = df.to_dict(orient="records")
    return records


# Module-level singleton loaded at import time
LISTINGS: list[dict] = load_listings()