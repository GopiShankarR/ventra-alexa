from flask import Flask, request, jsonify
from flask_ask_sdk.skill_adapter import SkillAdapter
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
import requests
from math import radians, sin, cos, sqrt, atan2
from word2number import w2n

app = Flask(__name__)
skill_builder = SkillBuilder()

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

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.speak("Welcome to the Bus Tracker. Ask me how far the bus is from you.").response

class SetLocationIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("SetLocationIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        try:
            lat_num = w2n.word_to_num(slots["lat"].value)
            long_num = w2n.word_to_num(slots["long"].value)
            user_location["latitude"] = lat_num
            user_location["longitude"] = long_num
            return handler_input.response_builder.speak(f"Your location is set to latitude {lat_num} and longitude {long_num}.").response
        except ValueError:
            return handler_input.response_builder.speak("I didn't understand the location. Please try again using numbers.").response

class GetMyLocationIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("GetMyLocationIntent")(handler_input)

    def handle(self, handler_input):
        lat = user_location.get("latitude")
        lon = user_location.get("longitude")

        if lat is None or lon is None:
            speech_text = "I don't have your location. Please set it first."
        else:
            speech_text = f"Your current latitude is {lat} and longitude is {lon}."

        return handler_input.response_builder.speak(speech_text).set_card(SimpleCard("Your Location", speech_text)).response

class GetBusTimeIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("GetBusTimeIntent")(handler_input)

    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        route_number = slots.get("routeNumber").value

        if not route_number:
            return handler_input.response_builder.speak("Please specify a bus route number.").response

        if not user_location["latitude"] or not user_location["longitude"]:
            return handler_input.response_builder.speak("I don't have your location. Please set it first.").response

        my_lat, my_lon = user_location["latitude"], user_location["longitude"]
        cta_api_key = "API_KEY"
        cta_url = f"http://www.ctabustracker.com/bustime/api/v2/getvehicles?key={cta_api_key}&rt={route_number}&tmres=m&format=json"
        response = requests.get(cta_url)

        if response.status_code != 200:
            return handler_input.response_builder.speak("I couldn't fetch bus data. Try again later.").response

        vehicle_data = response.json().get("bustime-response", {}).get("vehicle", [])
        if not vehicle_data:
            return handler_input.response_builder.speak(f"No buses found for route {route_number}.").response

        nearby_buses = []
        for vehicle in vehicle_data:
            bus_lat = float(vehicle["lat"])
            bus_lon = float(vehicle["lon"])
            distance = calculate_distance(my_lat, my_lon, bus_lat, bus_lon)
            travel_time = calculate_travel_time(distance)
            nearby_buses.append({"vid": vehicle["vid"], "time": travel_time})

        if nearby_buses:
            nearby_buses.sort(key=lambda x: x["time"])
            nearest_bus = nearby_buses[0]
            return handler_input.response_builder.speak(f"Bus {nearest_bus['vid']} is approximately {nearest_bus['time']:.2f} minutes away.").response
        else:
            return handler_input.response_builder.speak("No buses are near you right now.").response

skill_builder.add_request_handler(LaunchRequestHandler())
skill_builder.add_request_handler(SetLocationIntentHandler())
skill_builder.add_request_handler(GetBusTimeIntentHandler())
skill_builder.add_request_handler(GetMyLocationIntentHandler())

skill_adapter = SkillAdapter(skill=skill_builder.create(), skill_id="amzn1.ask.skill.YOUR_SKILL_ID", app=app)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "GET":
        return "Welcome to Bus Tracker App! Use the Alexa interface to interact."
    return "POST request received"

@app.route("/alexa", methods=["POST"])
def alexa_endpoint():
    return skill_adapter.dispatch_request()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)