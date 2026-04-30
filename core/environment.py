"""Environmental data: weather, sunrise/sunset, lunar phase."""
import requests
from datetime import datetime, timedelta
from astral import LocationInfo, moon
from astral.sun import sun
import math

NWS_BASE = "https://api.weather.gov"
USER_AGENT = "chicago-iching/1.0 (research)"


# ─────────────────────────────────────────────────────────────
# WEATHER (National Weather Service — free, no key)
# ─────────────────────────────────────────────────────────────

def get_weather(lat: float, lon: float, dt: datetime) -> dict:
    """
    Pull weather forecast or recent observation for given lat/lon and time.
    Returns a dict with temp, conditions, precipitation.
    """
    try:
        # Get the nearest forecast grid point
        r1 = requests.get(
            f"{NWS_BASE}/points/{lat:.4f},{lon:.4f}",
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        r1.raise_for_status()
        forecast_url = r1.json()["properties"]["forecastHourly"]

        # Get hourly forecast
        r2 = requests.get(
            forecast_url,
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        r2.raise_for_status()
        periods = r2.json()["properties"]["periods"]

        # Find the period closest to our target time
        target_iso = dt.isoformat()
        best = min(
            periods,
            key=lambda p: abs(
                (datetime.fromisoformat(
                    p["startTime"].replace("Z", "+00:00").split("+")[0]
                ) - dt).total_seconds()
            ),
        )

        return {
            "temp_f":      best["temperature"],
            "conditions":  best["shortForecast"],
            "is_daytime":  best.get("isDaytime", True),
            "wind":        best.get("windSpeed", "?"),
            "precipitation": (
                best.get("probabilityOfPrecipitation", {}).get("value")
                or 0
            ),
            "source":      "NWS",
        }
    except Exception as e:
        print(f"[weather] error: {e}")
        return {
            "temp_f":      None,
            "conditions":  "Unknown",
            "is_daytime":  None,
            "wind":        "?",
            "precipitation": 0,
            "source":      "unavailable",
        }


def weather_risk_modifier(weather: dict) -> int:
    """
    Convert weather into a risk score adjustment (-15 to +15).
    Based on criminology research:
    - Hot summer nights: more violent crime
    - Heavy rain: less outdoor crime
    - Pleasant weather: higher pedestrian traffic
    """
    if weather["temp_f"] is None:
        return 0

    mod = 0
    temp = weather["temp_f"]
    cond = weather["conditions"].lower()
    precip = weather.get("precipitation", 0) or 0

    # Temperature effects
    if temp >= 80:
        mod += 8        # Hot weather → more outdoor activity & friction
    elif temp >= 70:
        mod += 4
    elif temp <= 25:
        mod -= 5        # Bitter cold → fewer people out
    elif temp <= 35:
        mod -= 2

    # Precipitation effects
    if precip >= 60:
        mod -= 8        # Heavy rain → less outdoor crime
    elif precip >= 30:
        mod -= 3

    # Specific conditions
    if "thunder" in cond or "storm" in cond:
        mod -= 5
    if "snow" in cond:
        mod -= 3
    if "clear" in cond and weather.get("is_daytime") is False:
        mod += 2        # Clear nights → visibility for both crime & response

    return max(-15, min(15, mod))


# ─────────────────────────────────────────────────────────────
# SUN (sunrise / sunset / darkness)
# ─────────────────────────────────────────────────────────────

def get_sun_info(lat: float, lon: float, dt: datetime) -> dict:
    """Return sunrise, sunset, and whether the target time is dark."""
    try:
        loc = LocationInfo(
            "target", "USA", "America/Chicago", lat, lon
        )
        s = sun(loc.observer, date=dt.date(),
                tzinfo=loc.timezone)

        sunrise = s["sunrise"].replace(tzinfo=None)
        sunset  = s["sunset"].replace(tzinfo=None)
        dawn    = s["dawn"].replace(tzinfo=None)
        dusk    = s["dusk"].replace(tzinfo=None)

        is_dark = dt < dawn or dt > dusk

        # Hours past sunset (negative if before)
        hours_past_sunset = (dt - sunset).total_seconds() / 3600

        return {
            "sunrise":            sunrise,
            "sunset":             sunset,
            "is_dark":            is_dark,
            "hours_past_sunset":  round(hours_past_sunset, 1),
        }
    except Exception as e:
        print(f"[sun] error: {e}")
        return {
            "sunrise": None, "sunset": None,
            "is_dark": None, "hours_past_sunset": 0,
        }


def darkness_risk_modifier(sun_info: dict) -> int:
    """Crime tends to spike 2-6 hours after sunset."""
    if sun_info["is_dark"] is None:
        return 0

    if not sun_info["is_dark"]:
        return -3       # Daytime → slightly lower risk

    h = sun_info["hours_past_sunset"]
    if 2 <= h <= 6:
        return 12       # Peak crime window
    elif 0 < h < 2:
        return 6        # Just after dusk
    elif 6 < h < 10:
        return 8        # Late night
    elif h >= 10:
        return 5        # Early morning hours
    else:
        return 0


# ─────────────────────────────────────────────────────────────
# LUNAR (moon phase)
# ─────────────────────────────────────────────────────────────

def get_lunar(dt: datetime) -> dict:
    """Get lunar phase information for the given date."""
    try:
        phase_num = moon.phase(dt.date())   # 0-27.99
        # Astral phase: 0=new, 7=first qtr, 14=full, 21=last qtr

        if phase_num < 1.85:
            name, emoji = "New Moon", "🌑"
        elif phase_num < 5.54:
            name, emoji = "Waxing Crescent", "🌒"
        elif phase_num < 9.23:
            name, emoji = "First Quarter", "🌓"
        elif phase_num < 12.91:
            name, emoji = "Waxing Gibbous", "🌔"
        elif phase_num < 16.61:
            name, emoji = "Full Moon", "🌕"
        elif phase_num < 20.30:
            name, emoji = "Waning Gibbous", "🌖"
        elif phase_num < 23.99:
            name, emoji = "Last Quarter", "🌗"
        elif phase_num < 27.68:
            name, emoji = "Waning Crescent", "🌘"
        else:
            name, emoji = "New Moon", "🌑"

        # Illumination percentage (rough approx)
        illumination = round(
            50 * (1 - math.cos(2 * math.pi * phase_num / 28)), 1
        )

        return {
            "phase_num":    round(phase_num, 2),
            "phase_name":   name,
            "emoji":        emoji,
            "illumination": illumination,
            "is_full":      14 <= phase_num <= 16,
            "is_new":       phase_num < 1 or phase_num > 27,
        }
    except Exception as e:
        print(f"[lunar] error: {e}")
        return {
            "phase_num": 0, "phase_name": "Unknown",
            "emoji": "🌑", "illumination": 0,
            "is_full": False, "is_new": False,
        }


def lunar_risk_modifier(lunar: dict) -> int:
    """
    Folk wisdom + some research suggests crime spikes near full moons.
    Effect is small but real in some studies. Keep modifier modest.
    """
    if lunar["phase_name"] == "Unknown":
        return 0

    if lunar["is_full"]:
        return 4
    elif lunar["illumination"] >= 75:
        return 2
    elif lunar["is_new"]:
        return -2     # Darker night, but data on new moon is mixed
    else:
        return 0


# ─────────────────────────────────────────────────────────────
# UNIFIED ENVIRONMENT FETCH
# ─────────────────────────────────────────────────────────────

def get_environment(lat: float, lon: float, dt: datetime) -> dict:
    """Fetch all environmental data and total modifier."""
    weather = get_weather(lat, lon, dt)
    sun_info = get_sun_info(lat, lon, dt)
    lunar = get_lunar(dt)

    w_mod = weather_risk_modifier(weather)
    d_mod = darkness_risk_modifier(sun_info)
    l_mod = lunar_risk_modifier(lunar)

    return {
        "weather":     weather,
        "sun":         sun_info,
        "lunar":       lunar,
        "modifiers": {
            "weather":  w_mod,
            "darkness": d_mod,
            "lunar":    l_mod,
            "total":    w_mod + d_mod + l_mod,
        },
    }
