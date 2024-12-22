from flask import Flask
from flask_ask import Ask, statement
from math import radians, sin, cos, sqrt, atan2

# Flask app
app = Flask(__name__)
ask = Ask(app, "/")

# Haversine formula for distance calculation
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# Estimate travel time
def calculate_travel_time(distance_km, speed_kmh=32):  # Average speed ~32 km/h
    return (distance_km / speed_kmh) * 60  # Time in minutes

# Dummy data: Your location
my_lat, my_lon = 41.85, -87.62

# Dummy data: API response
vehicles = [
    {"lat": 41.851637, "lon": -87.619049, "vid": "1362", "pdist": 20267},
    {"lat": 41.811370, "lon": -87.616706, "vid": "8679", "pdist": 35053},
    {"lat": 41.721882, "lon": -87.618286, "vid": "7921", "pdist": 68853}
]

# Alexa Skill: Launch skill
@ask.launch
def launch_skill():
    return statement("Welcome to the Bus Tracker. Ask me how far the bus is from you.")

# Alexa Skill: Handle GetBusTimeIntent
@ask.intent("GetBusTimeIntent")
def get_bus_time():
    # Calculate distance and time for each bus
    nearby_buses = []
    for vehicle in vehicles:
        distance = calculate_distance(my_lat, my_lon, vehicle["lat"], vehicle["lon"])
        travel_time = calculate_travel_time(distance)
        nearby_buses.append({"vid": vehicle["vid"], "time": travel_time})

    # Respond with the nearest bus
    if nearby_buses:
        response = f"Bus {nearby_buses[0]['vid']} is approximately {nearby_buses[0]['time']:.2f} minutes away."
        return statement(response)
    else:
        return statement("No buses are near you at the moment.")

if __name__ == "__main__":
    app.run(debug=True)