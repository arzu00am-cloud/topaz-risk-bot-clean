import os
import requests

API_KEY = os.getenv("API_FOOTBALL_KEY")

print("API KEY:", API_KEY)

headers = {
    "x-apisports-key": API_KEY
}

r = requests.get(
    "https://v3.football.api-sports.io/status",
    headers=headers
)

print("STATUS CODE:", r.status_code)
print("RESPONSE:", r.text)
