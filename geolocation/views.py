import requests

from .models import PlaceCoordinates


def fetch_coordinates(apikey, address):
    base_url = "https://geocode-maps.yandex.ru/1.x"
    response = requests.get(
        base_url,
        params={
            "geocode": address,
            "apikey": apikey,
            "format": "json",
        },
    )
    response.raise_for_status()
    found_places = response.json()["response"]["GeoObjectCollection"]["featureMember"]
    if not found_places:
        return None
    most_relevant = found_places[0]
    lon, lat = most_relevant["GeoObject"]["Point"]["pos"].split(" ")
    return float(lat), float(lon)


def get_coordinates(address, apikey):
    cached = PlaceCoordinates.objects.filter(address=address).first()
    if cached and cached.lat is not None and cached.lon is not None:
        return cached.lat, cached.lon
    
    coords = fetch_coordinates(apikey, address)
    if coords:
        lat, lon = coords
        PlaceCoordinates.objects.update_or_create(
            address=address,
            defaults={"lat": lat, "lon": lon}
        )
        return lat, lon
    return None
