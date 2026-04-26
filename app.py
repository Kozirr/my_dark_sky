import os
import sys

from flask import Flask, render_template, request, jsonify

from config import Config
from models import db, Location
from weather_service import geocode, get_weather, get_forecast_strip

app = Flask(__name__)
app.config.from_object(Config)
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


@app.route("/api/weather")
def api_weather():
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
        date_str = request.args.get("date")
        data = get_weather(lat, lon, date_str)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/forecast")
def api_forecast():
    try:
        lat = float(request.args.get("lat"))
        lon = float(request.args.get("lon"))
        data = get_forecast_strip(lat, lon)
        return jsonify({"days": data})
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
