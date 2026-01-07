import os
import requests

RAPID_KEY = os.getenv("RAPIDAPI_KEY")
RAPID_HOST = os.getenv("RAPIDAPI_HOST")

print("KEY:", RAPID_KEY[:6], "****")
print("HOST:", RAPID_HOST)

headers = {
    "X-RapidAPI-Key": RAPID_KEY,
    "X-RapidAPI-Host": RAPID_HOST
}

r = requests.get(
    "https://api-football-v1.p.rapidapi.com/v3/fixtures?next=5",
    headers=headers
)

print("STATUS:", r.status_code)
print("RESPONSE:", r.text)
