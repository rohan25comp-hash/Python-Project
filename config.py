"""
config.py
Brand/model service-interval reference data for the Two-Wheeler
Service Reminder Manager.

NOTE: These intervals are approximate, commonly-quoted figures for
demonstration purposes. Always confirm the exact interval for a
specific model/year from the owner's manual or authorized dealer.
"""

SERVICE_INTERVALS = {
    "Bajaj": {
        "Pulsar 125":            {"km": 3000, "months": 3},
        "Pulsar 150":            {"km": 3000, "months": 3},
        "Pulsar NS200":          {"km": 3000, "months": 3},
        "Pulsar N250":           {"km": 3000, "months": 3},
        "Platina 100":           {"km": 3000, "months": 3},
        "Platina 110":           {"km": 3000, "months": 3},
        "Avenger Street 160":    {"km": 3000, "months": 3},
        "Avenger Cruise 220":    {"km": 3000, "months": 3},
        "Dominar 400":           {"km": 3000, "months": 3},
        "CT 100":                {"km": 3000, "months": 3},
        "Chetak (Electric)":     {"km": 5000, "months": 6},
    },
    "TVS": {
        "Apache RTR 160":        {"km": 3000, "months": 3},
        "Apache RTR 180":        {"km": 3000, "months": 3},
        "Apache RTR 200 4V":     {"km": 3000, "months": 3},
        "Apache RR 310":         {"km": 3000, "months": 3},
        "Jupiter":               {"km": 3000, "months": 4},
        "Jupiter 125":           {"km": 3000, "months": 4},
        "Ntorq 125":             {"km": 3000, "months": 3},
        "Star City Plus":        {"km": 3000, "months": 3},
        "Radeon":                {"km": 3000, "months": 3},
        "Raider 125":            {"km": 3000, "months": 3},
        "iQube (Electric)":      {"km": 5000, "months": 6},
    },
}

# Fallback for any model not explicitly listed above
DEFAULT_INTERVAL = {"km": 3000, "months": 3}

SERVICE_TYPES = [
    "General Service",
    "Oil Change",
    "Brake Inspection/Pad Change",
    "Chain/Belt Lubrication",
    "Tyre Change/Rotation",
    "Battery Check",
    "Air Filter Change",
    "Full/Major Service",
    "Other",
]

BRANDS = ["Bajaj", "TVS"]


def get_models(brand: str):
    """Return the list of known models for a brand."""
    return list(SERVICE_INTERVALS.get(brand, {}).keys())


def get_interval(brand: str, model: str) -> dict:
    """Return {'km': int, 'months': int} interval for a brand/model,
    falling back to a sensible default if the model isn't in our table."""
    return SERVICE_INTERVALS.get(brand, {}).get(model, DEFAULT_INTERVAL)
