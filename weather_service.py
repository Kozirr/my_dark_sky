import json
import os
import time

import requests
from datetime import datetime, timedelta

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
os.makedirs(CACHE_DIR, exist_ok=True)

WMO_CODES = {
    0: ("Clear sky", "sun"),
    1: ("Mainly clear", "sun-dim"),
    2: ("Partly cloudy", "cloud-sun"),
    3: ("Overcast", "cloud"),
    45: ("Fog", "cloud-fog"),
    48: ("Depositing rime fog", "cloud-fog"),
    51: ("Light drizzle", "cloud-drizzle"),
    53: ("Moderate drizzle", "cloud-drizzle"),
    55: ("Dense drizzle", "cloud-drizzle"),
    56: ("Light freezing drizzle", "cloud-drizzle"),
    57: ("Dense freezing drizzle", "cloud-drizzle"),
    61: ("Slight rain", "cloud-rain"),
    63: ("Moderate rain", "cloud-rain"),
    65: ("Heavy rain", "cloud-rain"),
    66: ("Light freezing rain", "cloud-rain"),
    67: ("Heavy freezing rain", "cloud-rain"),
    71: ("Slight snow fall", "snowflake"),
    73: ("Moderate snow fall", "snowflake"),
    75: ("Heavy snow fall", "snowflake"),
    77: ("Snow grains", "snowflake"),
    80: ("Slight rain showers", "cloud-rain"),
    81: ("Moderate rain showers", "cloud-rain"),
    82: ("Violent rain showers", "cloud-rain"),
    85: ("Slight snow showers", "snowflake"),
    86: ("Heavy snow showers", "snowflake"),
    95: ("Thunderstorm", "cloud-lightning"),
    96: ("Thunderstorm with slight hail", "cloud-lightning"),
    99: ("Thunderstorm with heavy hail", "cloud-lightning"),
}


def _cache_path(lat: float, lon: float, date_str: str) -> str:
    safe_lat = f"{lat:.4f}".replace(".", "_")
    safe_lon = f"{lon:.4f}".replace(".", "_")
    return os.path.join(CACHE_DIR, f"{safe_lat}_{safe_lon}_{date_str}.json")


def _get_cached(lat: float, lon: float, date_str: str, ttl: int = 300):
    path = _cache_path(lat, lon, date_str)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            entry = json.load(f)
        if time.time() - entry.get("cached_at", 0) < ttl:
            return entry["data"]
    except (json.JSONDecodeError, OSError):
        return None
    return None


def _set_cache(lat: float, lon: float, date_str: str, data: dict):
    path = _cache_path(lat, lon, date_str)
    entry = {"cached_at": time.time(), "data": data}
    try:
        with open(path, "w") as f:
            json.dump(entry, f)
    except OSError:
        pass


def wmo_to_info(code: int | None):
    if code is None:
        return ("Unknown", "help-circle")
    return WMO_CODES.get(code, ("Unknown", "help-circle"))


def geocode(query: str, count: int = 5):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": query, "count": count, "language": "en", "format": "json"}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    return [
        {
            "name": r.get("name"),
            "latitude": r.get("latitude"),
            "longitude": r.get("longitude"),
            "country": r.get("country"),
            "admin1": r.get("admin1"),
            "timezone": r.get("timezone"),
        }
        for r in results
    ]


def reverse_geocode(lat: float, lon: float) -> dict:
    url = "https://api.bigdatacloud.net/data/reverse-geocode-client"
    params = {
        "latitude": lat,
        "longitude": lon,
        "localityLanguage": "en",
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    city = data.get("city") or data.get("locality") or data.get("principalSubdivision")
    country = data.get("countryName")
    admin1 = data.get("principalSubdivision")
    if not city:
        return {"name": "My Location", "country": country, "admin1": admin1}
    return {
        "name": city,
        "country": country,
        "admin1": admin1,
    }


def _validate_coords(lat: float, lon: float):
    if not (-90 <= lat <= 90):
        raise ValueError(f"Latitude must be between -90 and 90, got {lat}")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Longitude must be between -180 and 180, got {lon}")


def _extract_hourly(api_data: dict) -> list[dict]:
    hourly = api_data.get("hourly", {})
    times = hourly.get("time", [])
    if not times:
        return []
    keys = [k for k in hourly.keys() if k != "time"]
    result = []
    for i, t in enumerate(times):
        entry = {"time": t[-5:] if len(t) >= 5 else t}
        for k in keys:
            values = hourly[k]
            entry[k] = values[i] if i < len(values) else None
        result.append(entry)
    return result


def _extract_daily(api_data: dict, date_str: str) -> dict:
    daily = api_data.get("daily", {})
    times = daily.get("time", [])
    if not times or date_str not in times:
        return {}
    idx = times.index(date_str)
    result = {}
    for k in daily.keys():
        if k == "time":
            continue
        values = daily[k]
        result[k] = values[idx] if idx < len(values) else None
    return result


def get_weather(lat: float, lon: float, date_str: str | None = None) -> dict:
    _validate_coords(lat, lon)

    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    try:
        target = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD.")

    today = datetime.now().date()
    max_future = today + timedelta(days=10)
    if target > max_future:
        raise ValueError(
            f"Date {date_str} is more than 10 days in the future. "
            f"Please select a date on or before {max_future.strftime('%Y-%m-%d')}."
        )

    cached = _get_cached(lat, lon, date_str)
    if cached is not None:
        return cached

    diff_days = (today - target).days

    current_vars = (
        "temperature_2m,relative_humidity_2m,apparent_temperature,is_day,"
        "precipitation,rain,showers,snowfall,weather_code,cloud_cover,"
        "pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m"
    )
    hourly_vars_forecast = (
        "temperature_2m,relative_humidity_2m,apparent_temperature,"
        "precipitation_probability,precipitation,weather_code,"
        "wind_speed_10m,wind_direction_10m"
    )
    hourly_vars_archive = (
        "temperature_2m,relative_humidity_2m,apparent_temperature,"
        "precipitation,weather_code,wind_speed_10m,wind_direction_10m"
    )
    daily_vars_forecast = (
        "weather_code,temperature_2m_max,temperature_2m_min,"
        "apparent_temperature_max,apparent_temperature_min,sunrise,sunset,"
        "precipitation_sum,precipitation_probability_max,wind_speed_10m_max"
    )
    daily_vars_archive = (
        "weather_code,temperature_2m_max,temperature_2m_min,"
        "apparent_temperature_max,apparent_temperature_min,sunrise,sunset,"
        "precipitation_sum,wind_speed_10m_max"
    )

    if diff_days <= 92 and diff_days >= -16:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": current_vars,
            "hourly": hourly_vars_forecast,
            "daily": daily_vars_forecast,
            "timezone": "auto",
            "start_date": date_str,
            "end_date": date_str,
        }
    else:
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": date_str,
            "end_date": date_str,
            "hourly": hourly_vars_archive,
            "daily": daily_vars_archive,
            "timezone": "auto",
        }

    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    api_data = resp.json()

    hourly_result = _extract_hourly(api_data)
    daily_result = _extract_daily(api_data, date_str)

    current = api_data.get("current")
    if current is None and hourly_result:
        noon_idx = min(
            range(len(hourly_result)),
            key=lambda i: abs(int(hourly_result[i]["time"][:2]) - 12),
        )
        noon = hourly_result[noon_idx]
        current = {
            "temperature_2m": noon.get("temperature_2m"),
            "relative_humidity_2m": noon.get("relative_humidity_2m"),
            "apparent_temperature": noon.get("apparent_temperature"),
            "is_day": 1,
            "precipitation": noon.get("precipitation"),
            "weather_code": noon.get("weather_code"),
            "cloud_cover": None,
            "pressure_msl": None,
            "surface_pressure": None,
            "wind_speed_10m": noon.get("wind_speed_10m"),
            "wind_direction_10m": noon.get("wind_direction_10m"),
        }

    weather_code = None
    if current and current.get("weather_code") is not None:
        weather_code = current["weather_code"]
    elif daily_result.get("weather_code") is not None:
        weather_code = daily_result["weather_code"]

    description, icon_name = wmo_to_info(weather_code)

    result = {
        "date": date_str,
        "current": current,
        "hourly": hourly_result,
        "daily": daily_result,
        "weather_description": description,
        "weather_icon": icon_name,
    }

    _set_cache(lat, lon, date_str, result)
    return result


def get_forecast_strip(lat: float, lon: float) -> list[dict]:
    _validate_coords(lat, lon)
    today = datetime.now().strftime("%Y-%m-%d")
    safe_lat = f"{lat:.4f}".replace(".", "_")
    safe_lon = f"{lon:.4f}".replace(".", "_")
    cache_key = f"{safe_lat}_{safe_lon}_strip"
    path = os.path.join(CACHE_DIR, f"{cache_key}.json")

    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                entry = json.load(f)
            if time.time() - entry.get("cached_at", 0) < 300:
                return entry["data"]
        except (json.JSONDecodeError, OSError):
            pass

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": (
            "weather_code,temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max"
        ),
        "timezone": "auto",
        "forecast_days": 14,
    }
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    days = []
    daily = data.get("daily", {})
    times = daily.get("time", [])
    for i, d in enumerate(times):
        code = daily["weather_code"][i] if i < len(daily["weather_code"]) else None
        info = wmo_to_info(code)
        days.append(
            {
                "date": d,
                "max_temp": daily["temperature_2m_max"][i]
                if i < len(daily["temperature_2m_max"])
                else None,
                "min_temp": daily["temperature_2m_min"][i]
                if i < len(daily["temperature_2m_min"])
                else None,
                "precip_prob": daily.get("precipitation_probability_max", [None] * 999)[i]
                if "precipitation_probability_max" in daily
                else None,
                "weather_code": code,
                "weather_description": info[0],
                "weather_icon": info[1],
            }
        )

    try:
        with open(path, "w") as f:
            json.dump({"cached_at": time.time(), "data": days}, f)
    except OSError:
        pass

    return days
