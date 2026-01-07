import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}

FIXTURES_URL = "https://v3.football.api-sports.io/fixtures"
STATS_URL = "https://v3.football.api-sports.io/teams/statistics"

# ================= ANALIZ =================
def calculate_probability(team_id, league_id, season):
    r = requests.get(
        STATS_URL,
        headers=HEADERS,
        params={
            "team": team_id,
            "league": league_id,
            "season": season
        }
    )

    if r.status_code != 200:
        return 50

    data = r.json().get("response")
    if not data:
        return 50

    wins = data["fixtures"]["wins"]["total"]
    played = data["fixtures"]["played"]["total"]

    if played == 0:
        return 50

    win_rate = (wins / played) * 100
    return min(int(win_rate), 85)

def get_best_games():
    from_date = datetime.utcnow()
    to_date = from_date + timedelta(days=2)

    r = requests.get(
        FIXTURES_URL,
        headers=HEADERS,
        params={
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d")
        }
    )

    if r.status_code != 200:
        return []

    games = []

    for g in r.json().get("response", []):
        league_id = g["league"]["id"]
        season = g["league"]["season"]

        home = g["teams"]["home"]
        away = g["teams"]["away"]

        home_prob = calculate_probability(home["id"], league_id, season)
        away_prob = calculate_probability(away["id"], league_id, season)

        best_prob = max(home_prob, away_prob)

        games.append({
            "league": g["league"]["name"],
            "match": f"{home['name']} vs {away['name']}",
            "prob": best_prob
        })

    games.sort(key=lambda x: x["prob"], reverse=True)
    return games[:3]

# ================= TELEGRAM =================
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 Real analiz edilir...\n⏳ Bir neçə saniyə gözlə"
    )

    games = get_best_games()

    if not games:
        await update.message.reply_text(
            "❌ Yaxın 48 saat üçün uyğun real oyun tapılmadı"
        )
        return

    msg = "⚽ Bugünkü ƏN UĞURLU 3 OYUN:\n\n"

    for g in games:
        msg += (
            f"{g['league']}\n"
            f"{g['match']}\n"
            f"Uğurlu olma ehtimalı: {g['prob']}%\n\n"
        )

    await update.message.reply_text(msg)

# ================= START =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("today", today))
    app.run_polling()

if __name__ == "__main__":
    main()
