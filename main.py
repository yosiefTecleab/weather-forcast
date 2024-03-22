import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
import requests
import csv


def fetch_weather_data(latitude, longitude):

  CLIENT_ID = "83ff59d0-b168-4e05-88af-70d2412d2799"
  url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={latitude}&lon={longitude}"
  headers = {"User-Agent": "Weather service"}
  response = requests.get(url, auth=(CLIENT_ID, ''), headers=headers)

  if response.status_code == 200:
    return response.json()
  else:
    return None


def parse_weather_data(data):
  forecasts = []
  weather_descr = weather_description('legend_translate.csv')
  for forecast in data['properties']['timeseries'][:24]:
    time = datetime.fromisoformat(forecast['time'].rstrip('Z'))
    temperature = forecast['data']['instant']['details']['air_temperature']
    wind_speed = forecast['data']['instant']['details']['wind_speed']
    wind_direction = forecast['data']['instant']['details'][
        'wind_from_direction']
    symbol_code = forecast['data']['next_1_hours']['summary']['symbol_code']

    forecasts.append({
        'Tid':
        time,
        'Temperatur (°C)':
        temperature,
        'Vind (m/s)':
        wind_speed,
        'Vindkast':
        wind_direction,
        'Værforhold':
        weather_descr[str(symbol_code).split('_')[0]]
        #'Værforhold': weather_descr[str(symbol_code)]

        # 'Værforhold': symbol_code
    })
  return forecasts


def average_parse_weather_data(data):
  daily_forecasts = {}
  for forecast in data['properties']['timeseries']:
    time = datetime.fromisoformat(forecast['time'].rstrip('Z'))
    date = time.date()
    temperature = forecast['data']['instant']['details']['air_temperature']
    wind_speed = forecast['data']['instant']['details']['wind_speed']
    if date in daily_forecasts:
      daily_forecasts[date]['temperature'].append(temperature)
      daily_forecasts[date]['wind_speed'].append(wind_speed)
    else:
      daily_forecasts[date] = {
          'temperature': [temperature],
          'wind_speed': [wind_speed]
      }
  daily_averages = []
  for date, values in daily_forecasts.items():
    daily_average_temperature = round(
        sum(values['temperature']) / len(values['temperature']), 1)
    daily_average_wind_speed = round(
        sum(values['wind_speed']) / len(values['wind_speed']), 1)
    daily_averages.append({
        'Dato': date,
        'Temperature (°C)': daily_average_temperature,
        'Vind (m/s)': daily_average_wind_speed
    })
  return daily_averages


def get_lat_lon(city):
  geolocator = Nominatim(user_agent="weather_data")
  location = geolocator.geocode(city)
  if location:
    return location.latitude, location.longitude
  else:
    return None, None


def convert_wind_direction(degrees):
  arrows = {
      0: ('↓', 'nord'),
      45: ('↙', 'nordøst'),
      90: ('←', 'øst'),
      135: ('↖', 'sørøst'),
      180: ('↑', 'sør'),
      225: ('↗', 'sørvest'),
      270: ('→', 'vest'),
      315: ('↘', 'nordvest'),
  }
  closest = min(arrows.keys(), key=lambda x: abs(x - degrees))
  return arrows[closest]


def get_weather_icon(symbol_code):
  # Here, you can map symbol codes to the respective weather icons
  # For example, you can have a dictionary with symbol codes as keys and icon filenames as values
  # Make sure to have weather icons stored in a folder named "weather-icons" within your project directory
  icon_mapping = {
      'clearsky_day': 'clearsky_day.png',
      # Add more mappings for other weather conditions
  }
  #icon_filename = icon_mapping.get(symbol_code, 'unknown.png')  # Default to unknown icon if symbol code not found
  icon_filename = icon_mapping.get(
      symbol_code,
      'clearsky_day.png')  # Default to unknown icon if symbol code not found

  return f"weather-icons/{icon_filename}"


def weather_description(csv_file_path):

  symbol_bokmal_dict = {}

  with open(csv_file_path, mode='r', encoding='utf-8-sig') as file:
    csv_reader = csv.DictReader(file)
    for row in csv_reader:
      symbol_bokmal_dict[row['Symbol_ID']] = row['Bokmål']

  return symbol_bokmal_dict


st.title("Værvarsel")

city = st.text_input("Skriv inn navnet på byen eller stedet:")

#"Hente værdata"
if st.button("Hent værdata for hele dagen"):
  latitude, longitude = get_lat_lon(city)
  if latitude is not None and longitude is not None:
    data = fetch_weather_data(latitude, longitude)
    if data:
      forecasts = parse_weather_data(data)
      df = pd.DataFrame(forecasts)
      df['Vindkast'] = df['Vindkast'].apply(
          lambda x: convert_wind_direction(x))
      st.write(f"Være i {city}")
      #  for index, row in df.iterrows():
      #   weather_icon = get_weather_icon(row['Symbol Code'])
      #  st.image(weather_icon, width=50)
      st.dataframe(df.set_index('Tid'))
    else:
      st.error("Failed to fetch weather data.")
  else:
    st.error("Location not found.")

if st.button("Hent værdata for neste 7 dager"):
  latitude, longitude = get_lat_lon(city)
  if latitude is not None and longitude is not None:
    data = fetch_weather_data(latitude, longitude)
    if data:
      daily_forecasts = average_parse_weather_data(data)
      df = pd.DataFrame(daily_forecasts)
      df.set_index('Dato', inplace=True)
      st.write(f"Daglig Være i {city}")
      st.dataframe(df)
    else:
      st.error("Failed to fetch weather data.")
  else:
    st.error("Location not found.")
