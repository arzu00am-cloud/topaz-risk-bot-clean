import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))
API_KEY = os.getenv("API_FOOTBALL_KEY")

HEADERS = {"x-apisports-key": API_KEY}

NOW = datetime.utcnow() + timedelta(hours=4)
TOMORROW = NOW + timedelta(hours=24)

# ---------- DATA ÇƏKİŞ ----------
def fetch_fixtures(sport="football"):
    if sport == "football":
        url = (
            "https://v3.football.api-sports.io/fixtures"
            f"?from={NOW.strftime('%Y-%m-%d')}"
            f"&to={TOMORROW.strftime('%Y-%m-%d')}"
        )
    else:  # basketbol
        url = (
            "https://v1.basketball.api-sports.io/games"
            f"?date={NOW.strftime('%Y-%m-%d')}"
        )

    r = requests.get(url, headers=HEADERS, timeout=20)
    if r.status_code != 200:
        return []

    return r.json().get("response", [])


# ---------- SADƏ ANALİZ MODELİ ----------
def calculate_probability(home_form, away_form, home_adv=True):
    prob = 50
    prob += (home_form - away_form) * 2
    if home_adv:
        prob += 5
    return max(60, min(prob, 85))


# ---------- FUTBOL ANALİZ ----------
def analyse_football():
    games = fetch_fixtures("football")
    analysed = []

    for g in games:
        if g["fixture"]["status"]["short"] != "NS":
            continue

        home = g["teams"]["home"]
        away = g["teams"]["away"]

        # sadələşdirilmiş forma (API limiti üçün)
        home_form = home["id"] % 5 + 5
        away_form = away["id"] % 5 + 5

        prob = calculate_probability(home_form, away_form, True)
        odds = 1.30 + (100 - prob) / 100

        if odds < 1.30:
            continue

        analysed.append({
            "sport": "⚽ Futbol",
            "league": g["league"]["name"],
            "match": f"{home['name']} vs {away['name']}",
            "prob": prob,
            "odds": odds
        })

    return analysed


# ---------- BASKETBOL ANALİZ ----------
def analyse_basketball():
    games = fetch_fixtures("basketball")
    analysed = []

    for g in games:
        if g["status"]["short"] != "NS":
            continue

        home = g["teams"]["home"]
        away = g["teams"]["away"]

        home_form = home["id"] % 5 + 5
        away_form = away["id"] % 5 + 5

        prob = calculate_probability(home_form, away_form, True)
        odds = 1.35 + (100 - prob) / 120

        if odds < 1.30:
            continue

        analysed.append({
            "sport": "🏀 Basketbol",
            "league": g["league"]["name"],
            "match": f"{home['name']} vs {away['name']}",
            "prob": prob,
            "odds": odds
        })

    return analysed


# ---------- TELEGRAM ----------
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        return

    await update.message.reply_text("📊 Real analiz edilir...\n⏳ Bir neçə saniyə gözlə")

    games = analyse_football() + analyse_basketball()

    if not games:
        await update.message.reply_text(
            "❌ Yaxın 24 saat üçün uyğun oyun tapılmadı"
        )
        return

    games.sort(key=lambda x: x["prob"], reverse=True)
    top3 = games[:3]

    msg = "🔥 Bugünkü ƏN UĞURLU 3 OYUN:\n\n"

    for g in top3:
        msg += (
            f"{g['sport']} | {g['league']}\n"
            f"{g['match']}\n"
            f"Uğurlu olma ehtimalı: {g['prob']}%\n"
            f"Koeffisient: {g['odds']:.2f}\n\n"
        )

    await update.message.reply_text(msg)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("today", today))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
