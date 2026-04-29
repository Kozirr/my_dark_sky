# Welcome to My Dark Sky
***

## Task
Rebuild the award-winning Dark Sky weather experience as a production-grade Flask web application that delivers current weather and forecasts for any location on Earth. The app needed a stunning UI, a robust caching layer to minimize API calls, date navigation for historical and future weather, and strict automated evaluation criteria including command-line argument handling.

## Description
Architected a dual-purpose Python application (`app.py`) that functions both as a CLI tool for the auto-grader and as a production-grade Flask web server.

The backend uses **Flask** to serve a RESTful API and render the frontend, **Open-Meteo API** for all weather data (free, no API key, with real-time, forecast, and historical archive support), a **JSON File Cache** with a 5-minute TTL to reduce redundant calls, and **SQLite + SQLAlchemy** to persist geocoded locations. The frontend uses **Tailwind CSS** for a responsive glassmorphism dark-mode dashboard, **Chart.js** for interactive hourly charts, and **Lucide Icons** for weather iconography.

Key features include browser geolocation with reverse geocoding, real-time city search with dropdown suggestions, a large-format current weather display, seamless switching between forecast and historical archive APIs based on the selected date, and a 14-day forecast strip with quick navigation.

## Installation
```bash
git clone git@git.us.qwasar.io:my_dark_sky_211575_cz313y/my_dark_sky.git
cd my_dark_sky
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage
```bash
python app.py
```
Then open `http://localhost:5000` in your browser.

### The Core Team


<span><i>Made at <a href='https://qwasar.io'>Qwasar SV -- Software Engineering School</a></i></span>
<span><img alt='Qwasar SV -- Software Engineering School's Logo' src='https://storage.googleapis.com/qwasar-public/qwasar-logo_50x50.png' width='20px' /></span>
