import os
import requests
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY")
USER_ID = int(os.getenv("USER_ID"))

HEADERS = {
    "x-apisports-key": API_KEY
}

# Bakı vaxtı
NOW = datetime.utcnow() + timedelta(hours=4)
TODAY = NOW.strftime("%Y-%m-%d")
TOMORROW = (NOW + timedelta(days=1)).strftime("%Y-%m-%d")


def get_fixtures():
    url = f"https://v3.football.api-sports.io/fixtures?from={TODAY}&to={TOMORROW}&status=NS"
    r = requests.get(url, headers=HEADERS, timeout=15)
    if r.status_code != 200:
        return []
    return r.json().get("response", [])


def analyze_game(game):
    home_id = game["teams"]["home"]["id"]
    away_id = game["teams"]["away"]["id"]
    league_id = game["league"]["id"]

    stats_url = (
        f"https://v3.football.api-sports.io/teams/statistics"
        f"?league={league_id}&season={NOW.year}&team={home_id}"
    )

    r = requests.get(stats_url, headers=HEADERS, timeout=15)
    if r.status_code != 200:
        return None

    data = r.json().get("response")
    if not data:
        return None

    win_rate = data["fixtures"]["wins"]["total"]
    played = data["fixtures"]["played"]["total"]

    if played == 0:
        return None

    probability = int((win_rate / played) * 100)

    # sadə koeffisient modeli
    odds = round(1.3 + (100 - probability) / 100, 2)

    if odds < 1.30:
        return None

    return probability, odds


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        return

    await update.message.reply_text(
        "📊 Analiz edilir...\n⏳ Real oyunlar yoxlanılır"
    )

    fixtures = get_fixtures()
    results = []

    for game in fixtures:
        analysis = analyze_game(game)
        if not analysis:
            continue

        probability, odds = analysis

        results.append({
            "league": game["league"]["name"],
            "home": game["teams"]["home"]["name"],
            "away": game["teams"]["away"]["name"],
            "prob": probability,
            "odds": odds
        })

    if not results:
        await update.message.reply_text("❌ Yaxın 24 saat üçün uyğun oyun tapılmadı")
        return

    results.sort(key=lambda x: x["prob"], reverse=True)
    top3 = results[:3]

    msg = "⚽ Yaxın 24 saat üçün ƏN UĞURLU 3 OYUN:\n\n"

    for g in top3:
        msg += (
            f"{g['league']}:\n"
            f"{g['home']} vs {g['away']}\n"
            f"Uğurlu olma ehtimalı: {g['prob']}%\n"
            f"Bet koeffisienti: {g['odds']}\n\n"
        )

    await update.message.reply_text(msg)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("today", today))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
