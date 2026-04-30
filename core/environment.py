"""Environmental data: weather, sunrise/sunset, lunar phase."""
import requests
from datetime import datetime
from astral import LocationInfo, moon
from astral.sun import sun
import math


# ─────────────────────────────────────────────────────────────
# WEATHER (Open-Meteo — free, no key, historical + forecast)
# ─────────────────────────────────────────────────────────────

def get_weather(lat: float, lon: float, dt: datetime) -> dict:
    """Pull weather (historical or forecast) using Open-Meteo."""
    try:
        date_str = dt.strftime("%Y-%m-%d")
        hour = dt.hour
        now = datetime.now()

        if dt.date() < now.date():
            url = "https://archive-api.open-meteo.com/v1/archive"
        else:
            url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": date_str,
            "end_date": date_str,
            "hourly": "temperature_2m,precipitation,weather_code,wind_speed_10m",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "timezone": "America/Chicago",
        }

        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        hourly = data.get("hourly", {})
        if not hourly.get("temperature_2m"):
            return {
                "temp_f": None, "conditions": "No data",
                "is_daytime": None, "wind": "?",
                "precipitation": 0, "source": "Open-Meteo (no data)",
            }

        idx = min(hour, len(hourly["temperature_2m"]) - 1)
        temp = hourly["temperature_2m"][idx]
        precip = hourly["precipitation"][idx] or 0
        wind = hourly["wind_speed_10m"][idx] or 0
        code = hourly["weather_code"][idx] or 0

        conditions = _wmo_to_text(code)

        return {
            "temp_f": round(temp) if temp is not None else None,
            "conditions": conditions,
            "is_daytime": 6 <= hour <= 19,
            "wind": f"{round(wind)} mph",
            "precipitation": round(precip * 100) if precip < 1 else 100,
            "source": "Open-Meteo",
        }
    except Exception as e:
        print(f"[weather] error: {e}")
        return {
            "temp_f": None,
            "conditions": "Unknown",
            "is_daytime": None,
            "wind": "?",
            "precipitation": 0,
            "source": "unavailable",
        }


def _wmo_to_text(code: int) -> str:
    """Map WMO weather code to readable text."""
    mapping = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Foggy", 48: "Foggy",
        51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
        61: "Light rain", 63: "Rain", 65: "Heavy rain",
        71: "Light snow", 73: "Snow", 75: "Heavy snow",
        77: "Snow grains",
        80: "Light showers", 81: "Showers", 82: "Heavy showers",
        85: "Snow showers", 86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail", 99: "Severe thunderstorm",
    }
    return mapping.get(code, f"Code {code}")


def weather_risk_modifier(weather: dict) -> int:
    """Convert weather into a risk score adjustment (-15 to +15)."""
    if weather["temp_f"] is None:
        return 0

    mod = 0
    temp = weather["temp_f"]
    cond = weather["conditions"].lower()
    precip = weather.get("precipitation", 0) or 0

    if temp >= 80:
        mod += 8
    elif temp >= 70:
        mod += 4
    elif temp <= 25:
        mod -= 5
    elif temp <= 35:
        mod -= 2

    if precip >= 60:
        mod -= 8
    elif precip >= 30:
        mod -= 3

    if "thunder" in cond or "storm" in cond:
        mod -= 5
    if "snow" in cond:
        mod -= 3
    if "clear" in cond and weather.get("is_daytime") is False:
        mod += 2

    return max(-15, min(15, mod))


# ─────────────────────────────────────────────────────────────
# SUN (sunrise / sunset / darkness)
# ─────────────────────────────────────────────────────────────

def get_sun_info(lat: float, lon: float, dt: datetime) -> dict:
    """Return sunrise, sunset, and whether the target time is dark."""
    try:
        loc = LocationInfo("target", "USA", "America/Chicago", lat, lon)
        s = sun(loc.observer, date=dt.date(), tzinfo=loc.timezone)

        sunrise = s["sunrise"].replace(tzinfo=None)
        sunset = s["sunset"].replace(tzinfo=None)
        dawn = s["dawn"].replace(tzinfo=None)
        dusk = s["dusk"].replace(tzinfo=None)

        is_dark = dt < dawn or dt > dusk
        hours_past_sunset = (dt - sunset).total_seconds() / 3600

        return {
            "sunrise": sunrise,
            "sunset": sunset,
            "is_dark": is_dark,
            "hours_past_sunset": round(hours_past_sunset, 1),
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
        return -3

    h = sun_info["hours_past_sunset"]
    if 2 <= h <= 6:
        return 12
    elif 0 < h < 2:
        return 6
    elif 6 < h < 10:
        return 8
    elif h >= 10:
        return 5
    else:
        return 0


# ─────────────────────────────────────────────────────────────
# LUNAR (moon phase)
# ─────────────────────────────────────────────────────────────

def get_lunar(dt: datetime) -> dict:
    """Get lunar phase information for the given date."""
    try:
        phase_num = moon.phase(dt.date())

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

        illumination = round(
            50 * (1 - math.cos(2 * math.pi * phase_num / 28)), 1
        )

        return {
            "phase_num": round(phase_num, 2),
            "phase_name": name,
            "emoji": emoji,
            "illumination": illumination,
            "is_full": 14 <= phase_num <= 16,
            "is_new": phase_num < 1 or phase_num > 27,
        }
    except Exception as e:
        print(f"[lunar] error: {e}")
        return {
            "phase_num": 0, "phase_name": "Unknown",
            "emoji": "🌑", "illumination": 0,
            "is_full": False, "is_new": False,
        }


def lunar_risk_modifier(lunar: dict) -> int:
    """Folk wisdom + research suggests crime spikes near full moons."""
    if lunar["phase_name"] == "Unknown":
        return 0

    if lunar["is_full"]:
        return 4
    elif lunar["illumination"] >= 75:
        return 2
    elif lunar["is_new"]:
        return -2
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
        "weather": weather,
        "sun": sun_info,
        "lunar": lunar,
        "modifiers": {
            "weather": w_mod,
            "darkness": d_mod,
            "lunar": l_mod,
            "total": w_mod + d_mod + l_mod,
        },
    }
