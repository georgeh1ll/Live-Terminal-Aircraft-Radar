# Live Terminal Aircraft Radar

A **real-time terminal-based aircraft radar** displaying nearby flights and weather for **any location**. Track flights using latitude and longitude with a configurable radar range, all in your terminal.

<img width="911" height="273" alt="image" src="https://github.com/user-attachments/assets/f7adf75a-4d29-4d45-80f3-f95697711c6b" />
---

## Features

- Live aircraft tracking within a configurable radius around any coordinates.
- Terminal radar grid showing aircraft positions relative to the center.
- Aircraft information: **ID, Callsign, Distance, Altitude, Speed, Model**.
- Color-coded highlights:
  - **Magenta** – Emergency flights  
  - **Cyan** – Highlighted callsigns (e.g., UKP)  
  - **Red** – Military aircraft
- Live weather updates: temperature, wind, humidity, and weather description.
- ANSI color formatting for terminal visualization.
- Configurable refresh intervals for radar and weather data.
- Fully based on **open-source APIs**.

---

## Open Data Sources

This project uses publicly available and free APIs:

1. **[Airplanes Live API](https://api.airplanes.live/)**  
   Provides real-time aircraft positions around any latitude/longitude. This API is free for non-commercial use and aggregates ADS-B data, which is openly broadcast by aircraft.

2. **[Open-Meteo API](https://open-meteo.com/)**  
   Provides weather information such as temperature, wind, humidity, and weather conditions. Open-Meteo is open-source and free to use, with no API key required.

These sources allow anyone to build real-time tracking applications without relying on proprietary data.

---

## Installation

1. **Clone the repository**

```bash
git clone https://github.com/yourusername/live-terminal-radar.git
cd live-terminal-radar
```
2. **Install requirements**

```bash
pip install -r requirements.txt
```

3. **Change latitude, longtitude and search radius in Python file**
Open radar.py in text editor or IDE.
Change lines one and two to your location and preferred search radius.
Note only the 10 nearest aircraft will ever be shown. Aircraft on the ground and ground vehicles are not shown.  

```bash
LAT, LON = 51.50, 0.12        # Center coordinates
RADIUS_NM = 25                    # Radar range in nautical miles
```
4. **Run**
```bash
python radar.py
```

## License
MIT License © 2026 George Hill
