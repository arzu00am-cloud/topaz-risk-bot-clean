import os
import aiohttp
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import date

BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))
API_KEY = os.getenv("API_FOOTBALL_KEY")

async def fetch_fixtures():
    url = f"https://v3.football.api-sports.io/fixtures?date={date.today()}"
    headers = {"x-apisports-key": API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                return None, response.status
            data = await response.json()
            return data.get("response", []), 200

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        return

    await update.message.reply_text("📊 Analiz edilir...\n⏳ Bir neçə saniyə gözlə")

    fixtures, status = await fetch_fixtures()
    if fixtures is None:
        await update.message.reply_text(f"❌ API xətası: {status}")
        return

    if not fixtures:
        await update.message.reply_text("⚠️ Bugün oyun tapılmadı.")
        return

    # TOP 3 oyun
    top_games = fixtures[:3]

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
    main()
