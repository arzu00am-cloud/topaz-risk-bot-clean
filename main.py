import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import date

BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))
API_KEY = os.getenv("API_FOOTBALL_KEY")

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        return

    await update.message.reply_text("📊 Analiz edilir...\n⏳ Bir neçə saniyə gözlə")

    # 1️⃣ API-dən bugünkü futbol oyunlarını çəkmək
    url = f"https://v3.football.api-sports.io/fixtures?date={date.today()}"
    headers = {"x-apisports-key": API_KEY}
    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        await update.message.reply_text(f"❌ API xətası: {r.status_code}")
        return

    data = r.json()["response"]

    # 2️⃣ Sadəcə top 3 oyun
    top_games = data[:3]  # sadə, hələ statistik analiz əlavə olunmayıb

    msg = "⚽ Bugünkü TOP 3 futbol oyunları:\n\n"
    for g in top_games:
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
    main()test_api()
