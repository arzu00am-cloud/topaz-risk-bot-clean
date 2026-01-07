import requests

url = "https://api-football-v1.p.rapidapi.com/v3/status"

headers = {
    "X-RapidAPI-Key": "40ac533b0bmsh65451b8e37db835p108968jsn9a7377c82036",
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

r = requests.get(url, headers=headers)

print("STATUS:", r.status_code)
print("RESPONSE:", r.text)
