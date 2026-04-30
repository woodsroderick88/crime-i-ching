"""Empirical crime-risk engine — Chicago Open Data Portal."""
import requests
from datetime import datetime, timedelta
from collections import Counter

CHICAGO_API = "https://data.cityofchicago.org/resource/ijzp-q8t2.json"


def fetch_nearby_crimes(
    lat: float, lon: float, dt: datetime,
    radius_m: int = 1000, days: int = 90,
):
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
                "$select": (
                    "date,primary_type,description,"
                    "arrest,latitude,longitude"
                ),
            },
            timeout=15,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[empirical] API error: {e}")
        return []


def fetch_exact_window(
    lat: float, lon: float, dt: datetime,
    radius_m: int = 500, hours: int = 2,
):
    """Pull crimes within ±hours of dt (for scoring predictions)."""
    since = (dt - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S.000")
    until = (dt + timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S.000")
    where = (
        f"date >= '{since}' AND date <= '{until}' AND "
        f"within_circle(location, {lat}, {lon}, {radius_m})"
    )
    try:
        r = requests.get(
            CHICAGO_API,
            params={
                "$where": where,
                "$limit": 5000,
                "$select": "date,primary_type,latitude,longitude",
            },
            timeout=15,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"[empirical] exact-window error: {e}")
        return []


def compute_risk(
    lat: float, lon: float, dt: datetime,
    radius_m: int = 1000, days: int = 90,
    env_modifier: int = 0,   # NEW PARAMETER
):
    """Compute risk score, optionally adjusted by environmental modifier."""
    crimes = fetch_nearby_crimes(lat, lon, dt, radius_m, days)
    if not crimes:
        return {
            "score": 0, "base_score": 0, "env_modifier": 0,
            "top_types": [], "n_total": 0, "n_window": 0,
            "confidence": "none", "hour_match": 0, "raw": [],
        }

    target_hour = dt.hour
    hour_window = {
        (target_hour - 1) % 24,
        target_hour,
        (target_hour + 1) % 24,
    }
    in_window = [
        c for c in crimes
        if datetime.fromisoformat(c["date"]).hour in hour_window
    ]

    types = Counter(
        c.get("primary_type", "UNKNOWN") for c in in_window
    )
    total_in_window = sum(types.values()) or 1
    top3 = [
        {
            "type":  t.title(),
            "count": n,
            "pct":   round(100 * n / total_in_window, 1),
        }
        for t, n in types.most_common(3)
    ]

    events_per_day = len(in_window) / max(days, 1)
    base_score = min(100, int(events_per_day * 25))

    # Apply environmental modifier
    final_score = max(0, min(100, base_score + env_modifier))

    n = len(in_window)
    conf = "low" if n < 20 else ("moderate" if n < 100 else "high")

    return {
        "score":        final_score,
        "base_score":   base_score,
        "env_modifier": env_modifier,
        "top_types":    top3,
        "n_total":      len(crimes),
        "n_window":     n,
        "confidence":   conf,
        "hour_match":   n,
        "raw":          crimes[:500],
    }


def timing_label(score: int) -> str:
    if score >= 65: return "Bad–Bad ⚠️"
    if score >= 35: return "Mixed ⚖️"
    return "Good–Good ✅"
