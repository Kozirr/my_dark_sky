import os
import sys

from flask import Flask, render_template, request, jsonify

from config import Config
from models import db, Location
from weather_service import geocode, get_weather, get_forecast_strip, reverse_geocode

app = Flask(__name__)
app.config.from_object(Config)
Config.check_secret_key()
db.init_app(app)

with app.app_context():
    db.create_all()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/geocode")
def api_geocode():
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify({"results": []})
    try:
        results = geocode(q)
        for r in results:
            existing = Location.query.filter_by(
                latitude=r["latitude"], longitude=r["longitude"]
            ).first()
            if not existing:
                loc = Location(
                    name=r["name"],
                    latitude=r["latitude"],
                    longitude=r["longitude"],
                    country=r.get("country"),
                    admin1=r.get("admin1"),
                    timezone=r.get("timezone"),
                )
                db.session.add(loc)
        db.session.commit()
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _get_float_param(name: str, bounds: tuple | None = None):
    raw = request.args.get(name)
    if raw is None:
        raise ValueError(f"Missing required parameter: '{name}'")
    try:
        val = float(raw)
    except ValueError:
        raise ValueError(f"Parameter '{name}' must be a number, got '{raw}'")
    if bounds is not None:
        low, high = bounds
        if not (low <= val <= high):
            raise ValueError(f"Parameter '{name}' must be between {low} and {high}, got {val}")
    return val


@app.route("/api/reverse_geocode")
def api_reverse_geocode():
    try:
        lat = _get_float_param("lat", (-90, 90))
        lon = _get_float_param("lon", (-180, 180))
        data = reverse_geocode(lat, lon)
        return jsonify(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/weather")
def api_weather():
    try:
        lat = _get_float_param("lat", (-90, 90))
        lon = _get_float_param("lon", (-180, 180))
        date_str = request.args.get("date")
        data = get_weather(lat, lon, date_str)
        return jsonify(data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/forecast")
def api_forecast():
    try:
        lat = _get_float_param("lat", (-90, 90))
        lon = _get_float_param("lon", (-180, 180))
        data = get_forecast_strip(lat, lon)
        return jsonify({"days": data})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


application = app

if __name__ == "__main__":
    if len(sys.argv) == 3:
        firstname = sys.argv[1]
        lastname = sys.argv[2]
        print(f"{firstname}")
        print(f"{lastname}")
        sys.exit(0)
    elif len(sys.argv) == 1:
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port)
    else:
        print("Usage: python app.py <firstname> <lastname>")
        sys.exit(0)
