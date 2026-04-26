const API_BASE = "";
let currentLat = null;
let currentLon = null;
let currentLocationName = "Current Location";
let hourlyChart = null;

// Initialize app
document.addEventListener("DOMContentLoaded", () => {
    lucide.createIcons();
    setupEventListeners();
    initDatePicker();

    const saved = localStorage.getItem("lastLocation");
    if (saved) {
        const loc = JSON.parse(saved);
        loadWeather(loc.lat, loc.lon, loc.name);
    } else {
        // Default to Cambridge, MA — Dark Sky's original home
        loadWeather(42.3736, -71.1097, "Cambridge, MA");
    }
});

function setupEventListeners() {
    document.getElementById("locateBtn").addEventListener("click", useMyLocation);
    document
        .getElementById("searchInput")
        .addEventListener("input", debounce(handleSearch, 300));
    document.getElementById("datePicker").addEventListener("change", (e) => {
        if (currentLat !== null && currentLon !== null) {
            loadWeather(currentLat, currentLon, currentLocationName, e.target.value);
        }
    });
    document
        .getElementById("prevDateBtn")
        .addEventListener("click", () => shiftDate(-1));
    document
        .getElementById("nextDateBtn")
        .addEventListener("click", () => shiftDate(1));

    document.addEventListener("click", (e) => {
        if (
            !e.target.closest("#searchInput") &&
            !e.target.closest("#searchResults")
        ) {
            document.getElementById("searchResults").classList.add("hidden");
        }
    });
}

function initDatePicker() {
    const picker = document.getElementById("datePicker");
    const today = new Date().toISOString().split("T")[0];
    picker.value = today;
    // No min / max allows time travel to any date
}

function shiftDate(days) {
    const picker = document.getElementById("datePicker");
    const d = new Date(picker.value);
    d.setDate(d.getDate() + days);
    picker.value = d.toISOString().split("T")[0];
    if (currentLat !== null && currentLon !== null) {
        loadWeather(currentLat, currentLon, currentLocationName, picker.value);
    }
}

function useMyLocation() {
    if (!navigator.geolocation) {
        showError("Geolocation is not supported by your browser.");
        return;
    }
    showLoading(true);
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            currentLocationName = "My Location";
            loadWeather(pos.coords.latitude, pos.coords.longitude, "My Location");
        },
        (err) => {
            showLoading(false);
            showError("Unable to retrieve your location.");
        }
    );
}

async function handleSearch(e) {
    const q = e.target.value.trim();
    const resultsDiv = document.getElementById("searchResults");
    if (q.length < 2) {
        resultsDiv.classList.add("hidden");
        return;
    }
    try {
        const res = await fetch(
            `${API_BASE}/api/geocode?q=${encodeURIComponent(q)}`
        );
        const data = await res.json();
        if (data.results && data.results.length > 0) {
            resultsDiv.innerHTML = data.results
                .map(
                    (r) => `
                <div class="px-4 py-3 hover:bg-slate-700/50 cursor-pointer border-b border-slate-700/50 last:border-0 transition-colors"
                     onclick="selectLocation(${r.latitude}, ${r.longitude}, '${escapeJsString(r.name + (r.country ? ", " + r.country : ""))}')">
                    <div class="font-medium text-sm text-slate-200">${r.name}${r.admin1 ? ", " + r.admin1 : ""}</div>
                    <div class="text-xs text-slate-500">${r.country || ""}</div>
                </div>
            `
                )
                .join("");
            resultsDiv.classList.remove("hidden");
        } else {
            resultsDiv.innerHTML =
                '<div class="px-4 py-3 text-sm text-slate-400">No results found</div>';
            resultsDiv.classList.remove("hidden");
        }
    } catch (err) {
        console.error(err);
    }
}

function escapeJsString(str) {
    return str.replace(/['"\\]/g, "\\$&").replace(/\n/g, "\\n").replace(/\r/g, "");
}

function selectLocation(lat, lon, name) {
    document.getElementById("searchResults").classList.add("hidden");
    document.getElementById("searchInput").value = "";
    currentLocationName = name;
    loadWeather(lat, lon, name);
}

async function loadWeather(lat, lon, name, date) {
    currentLat = lat;
    currentLon = lon;
    currentLocationName = name;
    localStorage.setItem(
        "lastLocation",
        JSON.stringify({ lat, lon, name })
    );

    if (!date) {
        date = document.getElementById("datePicker").value;
    } else {
        document.getElementById("datePicker").value = date;
    }

    showLoading(true);
    showError(false);

    try {
        const [weatherRes, forecastRes] = await Promise.all([
            fetch(`${API_BASE}/api/weather?lat=${lat}&lon=${lon}&date=${date}`),
            fetch(`${API_BASE}/api/forecast?lat=${lat}&lon=${lon}`),
        ]);

        if (!weatherRes.ok) throw new Error("Weather fetch failed");
        if (!forecastRes.ok) throw new Error("Forecast fetch failed");

        const weather = await weatherRes.json();
        const forecast = await forecastRes.json();

        renderWeather(weather, name, date);
        renderForecastStrip(forecast.days);
        showLoading(false);
    } catch (err) {
        console.error(err);
        showLoading(false);
        showError(err.message || "Failed to load weather data.");
    }
}

function renderWeather(data, name, date) {
    document.getElementById("weatherCard").classList.remove("hidden");
    document.getElementById("chartCard").classList.remove("hidden");
    document.getElementById("detailsCard").classList.remove("hidden");
    document.getElementById("forecastCard").classList.remove("hidden");

    document.getElementById("locationName").textContent = name;
    const d = new Date(date + "T00:00:00");
    document.getElementById("locationDate").textContent = d.toLocaleDateString(
        "en-US",
        { weekday: "long", year: "numeric", month: "long", day: "numeric" }
    );

    const current = data.current || {};
    const daily = data.daily || {};

    document.getElementById("mainTemp").textContent =
        current.temperature_2m != null
            ? Math.round(current.temperature_2m) + "°"
            : "--°";
    document.getElementById("weatherDesc").textContent =
        data.weather_description || "--";
    document.getElementById("tempHigh").textContent =
        daily.temperature_2m_max != null
            ? Math.round(daily.temperature_2m_max) + "°"
            : "--°";
    document.getElementById("tempLow").textContent =
        daily.temperature_2m_min != null
            ? Math.round(daily.temperature_2m_min) + "°"
            : "--°";

    const iconEl = document.getElementById("weatherIcon");
    iconEl.setAttribute("data-lucide", data.weather_icon || "sun");
    lucide.createIcons();

    document.getElementById("detailHumidity").textContent =
        current.relative_humidity_2m != null
            ? current.relative_humidity_2m + "%"
            : "--";
    document.getElementById("detailWind").textContent =
        current.wind_speed_10m != null
            ? Math.round(current.wind_speed_10m) + " km/h"
            : "--";
    document.getElementById("detailPrecip").textContent =
        current.precipitation != null
            ? current.precipitation + " mm"
            : "--";
    document.getElementById("detailPressure").textContent =
        current.surface_pressure != null
            ? Math.round(current.surface_pressure) + " hPa"
            : "--";

    renderHourlyChart(data.hourly || []);
}

function renderHourlyChart(hourlyData) {
    const ctx = document.getElementById("hourlyChart").getContext("2d");
    if (hourlyChart) hourlyChart.destroy();

    const labels = hourlyData.map((h) => h.time);
    const temps = hourlyData.map((h) => h.temperature_2m);
    const precipProbs = hourlyData.map((h) =>
        h.precipitation_probability != null ? h.precipitation_probability : 0
    );

    hourlyChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                {
                    label: "Temperature (°C)",
                    data: temps,
                    borderColor: "rgba(96, 165, 250, 0.8)",
                    backgroundColor: "rgba(96, 165, 250, 0.1)",
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    yAxisID: "y",
                },
                {
                    label: "Precip %",
                    data: precipProbs,
                    borderColor: "rgba(148, 163, 184, 0.4)",
                    backgroundColor: "transparent",
                    borderWidth: 1,
                    borderDash: [5, 5],
                    tension: 0.4,
                    yAxisID: "y1",
                    pointRadius: 0,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: "index", intersect: false },
            plugins: {
                legend: {
                    labels: { color: "#94a3b8", font: { size: 11 } },
                },
                tooltip: {
                    backgroundColor: "rgba(15, 23, 42, 0.9)",
                    titleColor: "#e2e8f0",
                    bodyColor: "#cbd5e1",
                    borderColor: "rgba(148, 163, 184, 0.2)",
                    borderWidth: 1,
                },
            },
            scales: {
                x: {
                    ticks: {
                        color: "#64748b",
                        font: { size: 10 },
                        maxTicksLimit: 8,
                    },
                    grid: { color: "rgba(148, 163, 184, 0.05)" },
                },
                y: {
                    ticks: { color: "#64748b", font: { size: 10 } },
                    grid: { color: "rgba(148, 163, 184, 0.05)" },
                },
                y1: {
                    position: "right",
                    ticks: {
                        color: "#64748b",
                        font: { size: 10 },
                        callback: (v) => v + "%",
                    },
                    grid: { display: false },
                    min: 0,
                    max: 100,
                },
            },
        },
    });
}

function renderForecastStrip(days) {
    const container = document.getElementById("forecastStrip");
    const todayStr = new Date().toISOString().split("T")[0];

    container.innerHTML = days
        .slice(0, 14)
        .map((day) => {
            const dateObj = new Date(day.date + "T00:00:00");
            const dayName =
                day.date === todayStr
                    ? "Today"
                    : dateObj.toLocaleDateString("en-US", { weekday: "short" });
            const dateNum = dateObj.toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
            });
            return `
            <div onclick="selectDate('${day.date}')" class="snap-start min-w-[80px] bg-slate-800/30 hover:bg-slate-700/40 rounded-xl p-3 text-center cursor-pointer transition-colors border border-transparent hover:border-slate-600/30">
                <div class="text-xs font-medium text-slate-300 mb-1">${dayName}</div>
                <div class="text-[10px] text-slate-500 mb-2">${dateNum}</div>
                <i data-lucide="${day.weather_icon || "sun"}" class="w-6 h-6 mx-auto mb-2 text-slate-300"></i>
                <div class="text-xs font-semibold text-slate-200">${day.max_temp != null ? Math.round(day.max_temp) + "°" : "--"}</div>
                <div class="text-[10px] text-slate-500">${day.min_temp != null ? Math.round(day.min_temp) + "°" : "--"}</div>
            </div>
        `;
        })
        .join("");
    lucide.createIcons();
}

function selectDate(dateStr) {
    document.getElementById("datePicker").value = dateStr;
    if (currentLat !== null && currentLon !== null) {
        loadWeather(currentLat, currentLon, currentLocationName, dateStr);
    }
}

function showLoading(show) {
    const el = document.getElementById("loadingState");
    if (show) el.classList.remove("hidden");
    else el.classList.add("hidden");
}

function showError(msg) {
    const el = document.getElementById("errorState");
    if (msg === false) {
        el.classList.add("hidden");
        return;
    }
    document.getElementById("errorMessage").textContent = msg;
    el.classList.remove("hidden");
    lucide.createIcons();
}

function debounce(fn, ms) {
    let t;
    return (...args) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...args), ms);
    };
}
