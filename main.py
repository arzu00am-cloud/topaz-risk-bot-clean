import requests

url = "https://api-football-v1.p.rapidapi.com/v3/status"

headers = {
    "X-RapidAPI-Key": "BURAYA_40_LA_BASLAYAN_KEY",
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

r = requests.get(url, headers=headers)

print("STATUS:", r.status_code)
print("RESPONSE:", r.text)
