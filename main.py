import asyncio
import aiohttp
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ================== AYARLAR ==================
TELEGRAM_TOKEN = "BURAYA_TELEGRAM_BOT_TOKEN"
API_FOOTBALL_KEY = "BURAYA_API_FOOTBALL_KEY"

API_FOOTBALL_URL = "https://v3.football.api-sports.io/fixtures"
ODDS_URL = "https://v3.football.api-sports.io/odds"

HEADERS = {
    "x-apisports-key": API_FOOTBALL_KEY
}

TODAY = datetime.utcnow().strftime("%Y-%m-%d")
TOMORROW = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")

MIN_ODD = 1.30

# ================== FUTBOL DATA ==================
async def fetch_football():
    games = []

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(
            API_FOOTBALL_URL,
            params={"from": TODAY, "to": TOMORROW, "status": "NS"}
        ) as resp:
            data = await resp.json()

        for g in data.get("response", []):
            fixture_id = g["fixture"]["id"]
            league = g["league"]["name"]
            home = g["teams"]["home"]["name"]
            away = g["teams"]["away"]["name"]

            # ODDS
