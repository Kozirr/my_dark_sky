# Welcome to My Dark Sky
***

## Task
Dark Sky was an award-winning weather app acquired by Apple that provided hyperlocal weather forecasts with minute-by-minute precision. After it shut down, there was a gap in the market for a beautiful, simple, and accurate weather visualization tool.

The challenge was to rebuild this experience from scratch using modern tools: creating a Flask-based web application that not only delivers current weather and forecasts for any location on Earth, but also allows users to "travel through time" — viewing historical weather data back to 1940 and future forecasts up to two weeks ahead. The app needed a stunning UI, a robust caching layer to minimize API calls, and had to pass strict automated evaluation criteria including command-line argument handling.

## Description
I solved the problem by architecting a dual-purpose Python application (`app.py`) that functions both as a CLI tool for the auto-grader and as a production-grade Flask web server.

**Backend:**
- **Flask** serves a RESTful API (`/api/weather`, `/api/forecast`, `/api/geocode`) and renders the frontend.
- **Open-Meteo API** powers all weather data — completely free, no API key required, with support for real-time, forecast, and historical archive queries.
- **JSON File Cache** stores every API response in `cache/` with a 5-minute TTL, dramatically reducing redundant calls.
- **SQLite + SQLAlchemy** persists geocoded search locations for fast reuse.

**Frontend:**
- **Tailwind CSS** provides a responsive, glassmorphism-styled dark-mode dashboard inspired by the original Dark Sky aesthetic.
- **Chart.js** renders interactive hourly temperature and precipitation charts.
- **Lucide Icons** deliver crisp, consistent weather iconography.
- **Time Travel UI**: a date picker and arrow navigation allow users to jump to any day — past, present, or future.

**Key Features:**
- **Current Location**: Uses the browser's Geolocation API.
- **Search**: Real-time city search with dropdown suggestions.
- **Today's Weather**: Large-format display with temperature, conditions, and details.
- **Forecast / Historical**: Seamless switching between future forecasts (forecast API) and historical archive data (archive API) based on the selected date.
- **14-Day Strip**: At-a-glance daily cards for quick navigation.

## Installation
```bash
git clone git@git.us.qwasar.io:my_dark_sky_211575_cz313y/my_dark_sky.git
cd my_dark_sky
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

### Web Application
```bash
python app.py
```
Then open `http://localhost:5000` in your browser.

### CLI Mode (Auto-grader)
```bash
./app.py argument1 argument2
```
Example:
```bash
python app.py John Doe
# Output:
# John
# Doe
```

### Render Deployment
Follow `DEPLOYMENT.md` to deploy to Render in 3 clicks. Then paste the live URL into `my_dark_sky_url.txt`.

### The Core Team


<span><i>Made at <a href='https://qwasar.io'>Qwasar SV -- Software Engineering School</a></i></span>
<span><img alt='Qwasar SV -- Software Engineering School's Logo' src='https://storage.googleapis.com/qwasar-public/qwasar-logo_50x50.png' width='20px' /></span>
