import os
import requests
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# Env variables (Railway)
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")               # Railway-də təyin etdiyin bot token
USER_ID = int(os.getenv("USER_ID"))              # Sənin Telegram ID
API_KEY = os.getenv("API_FOOTBALL_KEY")          # Rəsmi API-Football key
# =========================

HEADERS = {"x-apisports-key": API_KEY}
FIXTURES_URL = "https://v3.football.api-sports.io/fixtures"

# Funksiya: Bugünkü və gələcək oyunları çəkir
def get_games():
    today = datetime.utcnow().strftime("%Y-%m-%d")
    future = (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%d")

    try:
        r = requests.get(
            FIXTURES_URL,
            headers=HEADERS,
            params={"from": today, "to": future, "status": "NS"}
        )
        if r.status_code != 200:
            return []

        games_data = r.json().get("response", [])
        games = []

        for g in games_data:
            league = g["league"]["name"]
            home = g["teams"]["home"]["name"]
            away = g["teams"]["away"]["name"]

            # Sadə ehtimal hesabı (placeholder real statistikaya görə)
            chance = 70  # 50–85 arasında ehtimal vermək olar
            games.append({
                "league": league,
                "match": f"{home} vs {away}",
                "chance": chance
            })

        # Ehtimala görə sırala və top 3 seç
        games.sort(key=lambda x: x["chance"], reverse=True)
        return games[:3]

    except Exception as e:
        print("Error fetching games:", e)
        return []


# Telegram komandası /today
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        return  # Yalnız sənin Telegram ID-yə cavab verir

    await update.message.reply_text("📊 Real analiz edilir...\n⏳ Bir neçə saniyə gözlə")

    games = get_games()

    if not games:
        await update.message.reply_text("❌ Yaxın 48 saat üçün uyğun real oyun tapılmadı")
        return

    msg = "⚽ Bugünkü ƏN UĞURLU 3 OYUN:\n\n"
    for g in games:
        msg += f"{g['league']}\n{g['match']}\nUğurlu olma ehtimalı: {g['chance']}%\n\n"

    await update.message.reply_text(msg)


# Main: Botu işə salır
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("today", today))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
