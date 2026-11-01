import os
import time
import requests
import tkinter as tk
from tkinter import ttk, messagebox

# ==========================================
# WEATHER APP USING OPENWEATHERMAP API
# ==========================================

API_KEY = os.getenv("OPENWEATHER_API_KEY")

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# Cache weather data for 5 minutes
CACHE_DURATION = 300
weather_cache = {}


def get_weather(city):
    """
    Fetch weather data from OpenWeatherMap API.
    Returns temperature, humidity, and forecast.
    """

    city = city.strip()

    if not city:
        raise ValueError("Please enter a city name.")

    # Check cache
    if city.lower() in weather_cache:
        cached_data, timestamp = weather_cache[city.lower()]

        if time.time() - timestamp < CACHE_DURATION:
            return cached_data

    if not API_KEY:
        raise ValueError(
            "API key not found!\n"
            "Please set OPENWEATHER_API_KEY environment variable."
        )

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            timeout=10
        )

        # Handle HTTP errors
        if response.status_code == 401:
            raise ValueError(
                "Invalid API key or key not activated.\n"
                "Please check your API key."
            )

        elif response.status_code == 404:
            raise ValueError(
                "City not found!\n"
                "Please enter a valid city name."
            )

        response.raise_for_status()

        # Parse JSON response
        data = response.json()

        # Extract nested JSON data
        temperature = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        forecast = data["weather"][0]["description"].capitalize()
        city_name = data["name"]

        weather_data = {
            "city": city_name,
            "temperature": temperature,
            "humidity": humidity,
            "forecast": forecast
        }

        # Store data in cache
        weather_cache[city.lower()] = (
            weather_data,
            time.time()
        )

        return weather_data

    except requests.exceptions.Timeout:
        raise ValueError(
            "Request timed out. Please try again."
        )

    except requests.exceptions.ConnectionError:
        raise ValueError(
            "No internet connection. Please check your network."
        )

    except requests.exceptions.HTTPError:
        raise ValueError(
            "Unable to fetch weather data from the server."
        )

    except (KeyError, IndexError, TypeError):
        raise ValueError(
            "Unexpected API response format."
        )


# ==========================================
# TKINTER GUI
# ==========================================

def search_weather():
    """
    Get city input and display weather information.
    """

    city = city_entry.get()

    try:
        weather = get_weather(city)

        result_label.config(
            text=(
                f"Weather in {weather['city']}\n\n"
                f"Temperature: {weather['temperature']} °C\n"
                f"Humidity: {weather['humidity']}%\n"
                f"Forecast: {weather['forecast']}"
            ),
            fg="#1B5E20"
        )

    except ValueError as error:
        result_label.config(
            text=str(error),
            fg="#C62828"
        )


# ==========================================
# APPLICATION WINDOW
# ==========================================

root = tk.Tk()

root.title("Weather Forecast App")
root.geometry("450x430")
root.resizable(False, False)

root.configure(bg="#EAF4F4")

# Application heading
title_label = tk.Label(
    root,
    text="WEATHER FORECAST",
    font=("Arial", 20, "bold"),
    bg="#EAF4F4",
    fg="#164E63"
)

title_label.pack(pady=20)

# Subtitle
subtitle_label = tk.Label(
    root,
    text="Check temperature, humidity and forecast",
    font=("Arial", 10),
    bg="#EAF4F4",
    fg="#475569"
)

subtitle_label.pack()

# City input
city_entry = ttk.Entry(
    root,
    width=30,
    font=("Arial", 12)
)

city_entry.pack(pady=20)

city_entry.insert(0, "Pune")

# Search button
search_button = tk.Button(
    root,
    text="Get Weather",
    command=search_weather,
    font=("Arial", 12, "bold"),
    bg="#0F766E",
    fg="white",
    activebackground="#115E59",
    activeforeground="white",
    padx=20,
    pady=8,
    cursor="hand2"
)

search_button.pack()

# Weather result display
result_label = tk.Label(
    root,
    text="Enter a city and click Get Weather",
    font=("Arial", 13),
    bg="#FFFFFF",
    fg="#334155",
    width=35,
    height=8,
    relief="groove",
    justify="center",
    wraplength=350
)

result_label.pack(pady=25)

# Footer
footer_label = tk.Label(
    root,
    text="Powered by OpenWeatherMap API",
    font=("Arial", 9),
    bg="#EAF4F4",
    fg="#64748B"
)

footer_label.pack()

# Run application
root.mainloop()
API_KEY = os.getenv("OPENWEATHER_API_KEY")
