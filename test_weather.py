import os
from dotenv import load_dotenv
load_dotenv()

import requests

def test_weather(city):
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    print(f"API Key: {api_key}")
    if api_key:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        try:
            response = requests.get(url, timeout=5)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                temp = data.get("main", {}).get("temp", "N/A")
                description = data.get("weather", [{}])[0].get("description", "N/A")
                humidity = data.get("main", {}).get("humidity", "N/A")
                print(f"Weather in {city}: {description.capitalize()}, {temp}°C, Humidity: {humidity}%")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Exception: {e}")
    else:
        print("No API key found")

test_weather("Madibeng")