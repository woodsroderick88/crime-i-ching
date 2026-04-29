"""Convert street address to (lat, lon) using OpenStreetMap Nominatim (free)."""
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import time

_geocoder = Nominatim(user_agent="chicago_crime_iching/1.0")


def geocode(address: str, retries: int = 2):
    """
    Return (lat, lon, full_address) tuple, or None if not found.
    Auto-appends 'Chicago, IL' if not already present.
    """
    full = address if "chicago" in address.lower() else f"{address}, Chicago, IL"
    for attempt in range(retries + 1):
        try:
            loc = _geocoder.geocode(full, timeout=10)
            if loc:
                return (loc.latitude, loc.longitude, loc.address)
            return None
        except (GeocoderTimedOut, GeocoderUnavailable):
            if attempt < retries:
                time.sleep(1)
                continue
            return None
        except Exception as e:
            print(f"[geocoder] error: {e}")
            return None
    return None
