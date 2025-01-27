from flask import Flask, request
from flask_ask import Ask, statement, session
import requests
from math import radians, sin, cos, sqrt, atan2

app = Flask(__name__)
ask = Ask(app, "/")

user_location = {"latitude": None, "longitude": None}

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def calculate_travel_time(distance_km, speed_kmh=32):
    return (distance_km / speed_kmh) * 60

vehicles = [
    {"lat": 41.851637, "lon": -87.619049, "vid": "1362", "pdist": 20267},
    {"lat": 41.811370, "lon": -87.616706, "vid": "8679", "pdist": 35053},
    {"lat": 41.721882, "lon": -87.618286, "vid": "7921", "pdist": 68853}
]

@app.route("/", methods=["GET"])
def home():
    return "Welcome to Bus Tracker App! Use the Alexa interface to interact."

@ask.launch
def launch_skill():
    return statement("Welcome to the Bus Tracker. Ask me how far the bus is from you.")

@ask.intent("GetLocationIntent")
def get_location():
    device_id = session.context['System']['device']['deviceId']
    api_access_token = session.context['System']['apiAccessToken']
    api_endpoint = session.context['System']['apiEndpoint']

    headers = {"Authorization": f"Bearer {api_access_token}"}
    location_url = f"{api_endpoint}/v1/devices/{device_id}/settings/address"
    response = requests.get(location_url, headers=headers)

    if response.status_code == 200:
        location_data = response.json()
        latitude = location_data.get("latitude")
        longitude = location_data.get("longitude")

        if latitude and longitude:
            user_location["latitude"] = latitude
            user_location["longitude"] = longitude
            return statement(f"Your location is set to latitude {latitude} and longitude {longitude}.")
        else:
            return statement("I couldn't retrieve your location. Please check your permissions.")
    elif response.status_code == 403:
        return statement("Location permissions are not granted. Please enable location access in the Alexa app.")
    else:
        return statement("I couldn't fetch your location due to an error. Please try again later.")

@ask.intent("GetBusTimeIntent")
def get_bus_time():
    if not user_location["latitude"] or not user_location["longitude"]:
        return statement("Please set your location first using the Get Location command.")
    
    my_lat, my_lon = user_location["latitude"], user_location["longitude"]

    nearby_buses = []
    for vehicle in vehicles:
        distance = calculate_distance(my_lat, my_lon, vehicle["lat"], vehicle["lon"])
        travel_time = calculate_travel_time(distance)
        nearby_buses.append({"vid": vehicle["vid"], "time": travel_time})

    if nearby_buses:
        response = f"Bus {nearby_buses[0]['vid']} is approximately {nearby_buses[0]['time']:.2f} minutes away."
        return statement(response)
    else:
        return statement("No buses are near you at the moment.")

if __name__ == "__main__":
    app.run(debug=True)