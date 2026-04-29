"""Empirical crime-risk engine using Chicago Open Data Portal."""
import requests
from datetime import datetime, timedelta
from collections import Counter

CHICAGO_API = "https://data.cityofchicago.org/resource/ijzp-q8t2.json"


def fetch_nearby_crimes(lat: float, lon: float, dt: datetime,
                        radius_m: int = 1000, days: int = 90):
    """Pull crimes within radius/time window from Chicago Open Data Portal."""
    since = (dt - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00.000")
    where = (
        f"date >= '{since}' AND "
        f"within_circle(location, {lat}, {lon}, {radius_m})"
    )
    try:
        r = requests.get(
            CHICAGO_API,
            params={
                "$where": where,
                "$limit": 10000,
                "$select": "date,primary_type,description,arrest,latitude,longitude",
            },
            timeout=15,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[empirical] API error: {e}")
        return []


def compute_risk(lat: float, lon: float, dt: datetime,
                 radius_m: int = 1000, days: int = 90):
    """Return risk dict with score, top types, and confidence."""
    crimes = fetch_nearby_crimes(lat, lon, dt, radius_m, days)
    if not crimes:
        return {
            "score": 0,
            "top_types": [],
            "n_total": 0,
            "n_window": 0,
            "confidence": "none",
            "hour_match": 0,
            "raw": [],
        }

    # Filter to ±1 hour of target time
    target_hour = dt.hour
    hour_window = {(target_hour - 1) % 24, target_hour, (target_hour + 1) % 24}
    in_window = [
        c for c in crimes
        if datetime.fromisoformat(c["date"]).hour in hour_window
    ]

    # Type frequency
    types = Counter(c.get("primary_type", "UNKNOWN") for c in in_window)
    total_in_window = sum(types.values()) or 1
    top3 = [
        {"type": t.title(), "count": n, "pct": round(100 * n / total_in_window, 1)}
        for t, n in types.most_common(3)
    ]

    # Risk score: events per day in this geo+time slice
    events_per_day = len(in_window) / max(days, 1)
    score = min(100, int(events_per_day * 25))

    # Confidence
    n = len(in_window)
    if n < 20:
        conf = "low"
    elif n < 100:
        conf = "moderate"
    else:
        conf = "high"

    return {
        "score": score,
        "top_types": top3,
        "n_total": len(crimes),
        "n_window": n,
        "confidence": conf,
        "hour_match": len(in_window),
        "raw": crimes[:500],
    }


def timing_label(score: int) -> str:
    """Convert numeric score to user-facing label."""
    if score >= 65:
        return "Bad–Bad ⚠️"
    if score >= 35:
        return "Mixed ⚖️"
    return "Good–Good ✅"
