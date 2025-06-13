import requests
from dotenv import load_dotenv
import os


def fetch_coordinates(address):
    load_dotenv()
    base_url = "https://geocode-maps.yandex.ru/1.x"
    apikey = os.getenv('YANDEX_API')
    response = requests.get(base_url, params={
        "geocode": address,
        "apikey": apikey,
        "format": "json",
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(" ")
    return lon, lat


if __name__ == '__main__':
    print(fetch_coordinates(input()))
