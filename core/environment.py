def get_weather(lat: float, lon: float, dt: datetime) -> dict:
    """
    Pull weather (historical or forecast) using Open-Meteo (free, no key).
    Handles past, present, and future dates.
    """
    try:
        date_str = dt.strftime("%Y-%m-%d")
        hour = dt.hour
        now = datetime.now()
        
        # Choose archive (past) or forecast (today/future) endpoint
        if dt.date() < now.date():
            # Historical
            url = "https://archive-api.open-meteo.com/v1/archive"
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
        else:
            # Forecast (up to 16 days ahead)
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

        # Pick the hour closest to target
        idx = min(hour, len(hourly["temperature_2m"]) - 1)
        temp = hourly["temperature_2m"][idx]
        precip = hourly["precipitation"][idx] or 0
        wind = hourly["wind_speed_10m"][idx] or 0
        code = hourly["weather_code"][idx] or 0
        
        # Map WMO weather codes to readable conditions
        conditions = _wmo_to_text(code)
        
        return {
            "temp_f":      round(temp) if temp is not None else None,
            "conditions":  conditions,
            "is_daytime":  6 <= hour <= 19,  # rough Chicago approximation
            "wind":        f"{round(wind)} mph",
            "precipitation": round(precip * 100) if precip < 1 else 100,
            "source":      "Open-Meteo",
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
