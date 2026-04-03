LAT, LON = 51.50, 0.12
RADIUS_NM = 25
import requests
import time
from geopy.distance import geodesic
import math
from datetime import datetime
import sys
import re

# --- Configuration ---
ADSB_URL = f"https://api.airplanes.live/v2/point/{LAT}/{LON}/{RADIUS_NM}"
REFRESH_SECONDS = 10 
WEATHER_REFRESH_SECONDS = 900 
PAGE_SIZE = 10
print(ADSB_URL)

# --- ANSI Styling ---
BG_BLUE = "\033[44m"
BG_GRAY = "\033[100m"
WHITE = "\033[97m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
GREEN = "\033[92m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"
HOME = "\033[H"  
HIDE_CURSOR = "\033[?25l"

LAST_VALID_DATA = []
CURRENT_WEATHER = "Loading weather..."

# --- ANSI padding helpers ---
ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

def visible_len(s):
    return len(ansi_escape.sub('', s))

def pad_ansi(s, width, align='<'):
    raw_len = visible_len(s)
    padding = width - raw_len
    if padding <= 0: return s
    if align == '<': return s + ' ' * padding
    if align == '>': return ' ' * padding + s
    return s

# --- Helper functions ---
def knots_to_mph(knots):
    return round(knots * 1.15078) if knots else 0

def km_to_miles(km):
    return round(km * 0.621371, 1)

def get_row_color(ac):
    callsign = (ac.get("flight") or "").strip().upper()
    if ac.get("emergency", "").lower() != "none": return MAGENTA
    if callsign.startswith("UKP"): return CYAN 
    if (ac.get("dbFlags", 0) & 1) == 1 or ac.get("mil", False): return RED 
    return WHITE

def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dLon = lon2 - lon1
    y = math.sin(dLon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dLon)
    return (math.degrees(math.atan2(y, x)) + 360) % 360

def get_weather_desc(code):
    codes = {0: "Clear", 1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast", 45: "Fog", 48: "Rime Fog", 
             51: "Light Drizzle", 61: "Slight Rain", 71: "Slight Snow", 95: "Thunderstorm"}
    return codes.get(code, "Fair")

def get_radar_lines(aircraft_list):
    rows, cols = 11, 23
    grid = [[" " for _ in range(cols)] for _ in range(rows)]
    mid_r, mid_c = rows // 2, cols // 2
    for r in range(rows): grid[r][mid_c] = "│"
    for c in range(cols): grid[mid_r][c] = "─"
    grid[mid_r][mid_c] = f"{YELLOW}·{RESET}" 
    grid[0][mid_c], grid[rows-1][mid_c], grid[mid_r][0], grid[mid_r][cols-1] = "N", "S", "W", "E"
    
    for idx, ac in enumerate(aircraft_list[:PAGE_SIZE]):
        dist = ac.get('dist_val', 0)
        bearing = calculate_bearing(LAT, LON, ac.get("lat", LAT), ac.get("lon", LON))
        angle_rad = math.radians(bearing - 90)
        norm_dist = (dist / RADIUS_NM) * (rows // 2 - 1)
        r = int(mid_r + norm_dist * math.sin(angle_rad))
        c = int(mid_c + (norm_dist * 2.0) * math.cos(angle_rad))
        if 0 <= r < rows and 0 <= c < cols:
            grid[r][c] = f"{get_row_color(ac)}{BOLD}{str(idx + 1)[-1]}{RESET}"
    return ["".join(row) for row in grid]

# --- Main drawing function ---
def draw_interface(data, is_stale):
    sys.stdout.write(HOME)
    date_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    pulse = f"{(RED if is_stale else GREEN)}●{RESET}"
    radar_lines = get_radar_lines(data)

    branding = f"{BG_BLUE}{WHITE}{BOLD} LOCAL RADAR {RESET} {date_str}"
    mil_count = sum(1 for ac in data if ((ac.get('dbFlags', 0) & 1) or ac.get('mil')))
    stats = f"TOTAL: {len(data):<2} | MIL: {mil_count:<2} | {pulse}"
    sys.stdout.write(f"{branding}   {BOLD}{stats}{RESET}\n")

    headers = ['ID', 'CALLSIGN', 'DIST', 'ALTITUDE', 'SPEED', 'MODEL']
    col_widths = [4, 12, 10, 12, 12, 22]
    head_text = ''.join(pad_ansi(h, w) for h, w in zip(headers, col_widths))
    sys.stdout.write(f"{BG_GRAY}{BOLD}{head_text}{RESET}\n")

    for i in range(11):
        if i < 10 and i < len(data):
            ac = data[i]
            color = get_row_color(ac)
            call = (ac.get('flight') or 'N/A').strip()[:11]
            dist = f"{ac.get('dist_val')}mi"
            raw_alt = ac.get('alt_baro', 0)
            try: alt = f"{int(raw_alt):,}ft"
            except: alt = "0ft"
            spd = f"{knots_to_mph(ac.get('gs', 0))}mph"
            model_raw = (ac.get('desc') or ac.get('t') or '').upper()
            mdl = "" if model_raw == "UNK" or not model_raw else model_raw[:22]

            cols = [
                f"{WHITE}{i+1}{RESET}",
                f"{BOLD}{color}{call}{RESET}",
                dist,
                alt,
                spd,
                mdl
            ]
            info = ''.join(pad_ansi(c, w) for c, w in zip(cols, col_widths))
        else:
            info = ' ' * sum(col_widths)

        rad = radar_lines[i] if i < len(radar_lines) else ''
        sys.stdout.write(f"{info}   {rad}\n")

    sys.stdout.write(f"{CYAN}{CURRENT_WEATHER}{RESET}\n")
    sys.stdout.flush()

# --- Weather update ---
def update_weather():
    global CURRENT_WEATHER
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&wind_speed_unit=mph"
    try:
        r = requests.get(weather_url, timeout=5).json()['current']
        temp, hum, wind, desc = r['temperature_2m'], r['relative_humidity_2m'], r['wind_speed_10m'], get_weather_desc(r['weather_code'])
        CURRENT_WEATHER = f"{temp}°C {desc} | Wind: {wind}mph | Humidity: {hum}%"
    except: 
        CURRENT_WEATHER = "Weather unavailable"

# --- Main loop ---
def main():
    print("\033[2J")
    sys.stdout.write(HIDE_CURSOR)
    last_fetch, last_weather = 0, 0
    is_stale = False
    while True:
        now = time.time()
        if now - last_weather >= WEATHER_REFRESH_SECONDS:
            update_weather()
            last_weather = now
        if now - last_fetch >= REFRESH_SECONDS:
            try:
                r = requests.get(ADSB_URL, timeout=5)
                ac_data = r.json().get("ac", [])
                processed = []
                for ac in ac_data:
                    if not ac.get("lat") or str(ac.get("alt_baro")).lower() == "ground": 
                        continue
                    ac['dist_val'] = km_to_miles(geodesic((LAT, LON), (ac['lat'], ac['lon'])).km)
                    processed.append(ac)
                LAST_VALID_DATA[:] = sorted(processed, key=lambda x: x['dist_val'])[:10]
                is_stale, last_fetch = False, now
            except: 
                is_stale = True
        draw_interface(LAST_VALID_DATA, is_stale)
        time.sleep(1)

if __name__ == "__main__":
    try: 
        main()
    except KeyboardInterrupt: 
        sys.stdout.write("\033[?25h\n")