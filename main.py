import requests

API_KEY = "1f7e8ab5b3caabcb2a80a8dc9cb140f2"

r = requests.get(
    "https://v3.football.api-sports.io/status",
    headers={"x-apisports-key": API_KEY}
)

print(r.status_code)
print(r.text)import requests

API_KEY = "SİZİN_RƏSMİ_API_KEY"

r = requests.get(
    "https://v3.football.api-sports.io/status",
    headers={"x-apisports-key": API_KEY}
)

print(r.status_code)
print(r.text)
