import re

city_coords = {
    "New Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bengaluru": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Hyderabad": (17.3850, 78.4867),
    "Pune": (18.5204, 73.8567),
    "Ahmedabad": (23.0225, 72.5714),
}

def get_varied_coords(city, index):
    """Add small variations to coordinates for different stations"""
    base_lat, base_lon = city_coords.get(city, (28.6139, 77.2090))
    variation = (index % 20 - 10) * 0.005
    return round(base_lat + variation, 4), round(base_lon + variation, 4)

with open("ev_charging_station.sql", "r", encoding="utf-8") as f:
    content = f.read()

lines = content.split("\n")
new_lines = []
station_index = {}

for line in lines:
    if line.startswith("INSERT INTO ev_charging_stations_reduced"):
        city_match = re.search(r"'[^']+',\s*'([^']+)',\s*'(\d{6})'", line)
        if city_match:
            city = city_match.group(1)
            if city not in station_index:
                station_index[city] = 0
            lat, lon = get_varied_coords(city, station_index[city])
            station_index[city] += 1
            
            line = line.rstrip(");").rstrip()
            line += f", {lat}, {lon});"
    
    new_lines.append(line)

with open("ev_charging_station.sql", "w", encoding="utf-8") as f:
    f.write("\n".join(new_lines))

print("Updated SQL file with latitude and longitude coordinates")
