import os
import aiohttp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import date

BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))
API_KEY = os.getenv("API_FOOTBALL_KEY")

# --------- Sadə ehtimal hesablayıcı funksiya ---------
def calculate_probability(home_form, away_form, h2h, home_advantage):
    """
    Yüksək ehtimal → daha uğurlu oyun
    """
    score = (sum(home_form)/len(home_form) + sum(away_form)/len(away_form) + sum(h2h)/len(h2h) + home_advantage)/4
    return round(score * 100)

# --------- Async API çağırışı ---------
async def fetch_fixtures():
    url = f"https://v3.football.api-sports.io/fixtures?date={date.today()}"
    headers = {"x-apisports-key": API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                return None, response.status
            data = await response.json()
            return data.get("response", []), 200

# --------- Today funksiyası ---------
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

    games_with_probability = []
    for g in fixtures:
        # ---- Sadələşdirilmiş dummy data ----
        home_form = [1,1,0,1,1,1,0,1,1,1]
        away_form = [0,1,0,1,0,1,0,1,0,1]
        h2h = [1,0,1,0,1]
        home_advantage = 1 if g["teams"]["home"]["id"] else 0

        probability = calculate_probability(home_form, away_form, h2h, home_advantage)

        # ---- Bet koeffisienti filtr ----
        # Dummy: əmsal = 1.3 + probability/200 (sadə simulyasiya)
        odds = round(1.3 + probability/200, 2)
        if odds < 1.3:
            continue

        games_with_probability.append((probability, odds, g))

    if not games_with_probability:
        await update.message.reply_text("⚠️ Bu gün uyğun oyun tapılmadı (əmsal < 1.3)")
        return

    # Ən uğurlu 3 oyun
    games_with_probability.sort(reverse=True, key=lambda x: x[0])
    top_games = games_with_probability[:3]

    msg = "⚽ Bugünkü ən uğurlu 3 oyun:\n\n"
    for probability, odds, g in top_games:
        home = g["teams"]["home"]["name"]
        away = g["teams"]["away"]["name"]
        league = g["league"]["name"]
        msg += f"{league}: {home} vs {away}\nEhtimal: {probability}% | Bet koeffisienti: {odds}\n\n"

    await update.message.reply_text(msg)

# --------- Main ---------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("today", today))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
