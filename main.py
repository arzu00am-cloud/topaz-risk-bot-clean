import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))
API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {"x-apisports-key": API_KEY}
FIXTURES_URL = "https://v3.football.api-sports.io/fixtures"

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Real analiz edilir...\n⏳ Bir neçə saniyə gözlə")

    r = requests.get(FIXTURES_URL, headers=HEADERS, params={"date": "2026-01-07"})
    if r.status_code != 200:
        await update.message.reply_text(f"❌ API cavab vermədi: {r.status_code}")
        return

    data = r.json().get("response", [])
    if not data:
        await update.message.reply_text("❌ Yaxın 24 saat üçün oyun tapılmadı")
        return

    msg = "⚽ Bugünkü oyunlar:\n\n"
    for g in data[:3]:
        home = g["teams"]["home"]["name"]
        away = g["teams"]["away"]["name"]
        league = g["league"]["name"]
        msg += f"{league}: {home} vs {away}\n"

    await update.message.reply_text(msg)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("today", today))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
