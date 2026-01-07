import os
import requests
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# Railway env variables
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))
API_KEY = os.getenv("API_FOOTBALL_KEY")  # API-Football key
# =========================

HEADERS = {"x-apisports-key": API_KEY}
FIXTURES_URL = "https://v3.football.api-sports.io/fixtures"
STATS_URL = "https://v3.football.api-sports.io/teams/statistics"

def fetch_team_stats(team_id, league_id, season):
    """Son 5 oyun forması, qol ortalaması"""
    try:
        r = requests.get(STATS_URL, headers=HEADERS,
                         params={"team": team_id, "league": league_id, "season": season})
        if r.status_code != 200:
            return {"win_rate": 50, "avg_goals": 1.5}
        data = r.json().get("response")
        if not data:
            return {"win_rate": 50, "avg_goals": 1.5}

        played = data["fixtures"]["played"]["total"]
        wins = data["fixtures"]["wins"]["total"]
        goals = data["goals"]["for"]["total"]["total"]

        win_rate = min(int((wins / played) * 100), 85) if played else 50
        avg_goals = goals / played if played else 1.5
        return {"win_rate": win_rate, "avg_goals": avg_goals}
    except:
        return {"win_rate": 50, "avg_goals": 1.5}


def calculate_bets(home_stats, away_stats):
    """1X2, Over/Under, BTTS"""
    hw = home_stats["win_rate"]
    aw = away_stats["win_rate"]

    # 1X2
    if hw > aw:
        one_x_two = "1"
    elif aw > hw:
        one_x_two = "2"
    else:
        one_x_two = "X"

    # Over/Under 2.5
    total_goals = home_stats["avg_goals"] + away_stats["avg_goals"]
    over_under = "Over 2.5" if total_goals >= 2.5 else "Under 2.5"

    # BTTS
    btts = "Yes" if home_stats["avg_goals"] > 1 and away_stats["avg_goals"] > 1 else "No"

    # Ehtimal
    chance = max(hw, aw)

    return one_x_two, over_under, btts, chance


def get_top_games():
    now = datetime.utcnow()
    start_date = now.strftime("%Y-%m-%d")
    end_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    params = {
        "from": start_date,
        "to": end_date,
        "status": "NS"
    }

    try:
        r = requests.get(FIXTURES_URL, headers=HEADERS, params=params)
        if r.status_code != 200:
            print("API status:", r.status_code)
            return []

        data = r.json().get("response", [])
        games = []

        for g in data:
            league_id = g["league"]["id"]
            season = g["league"]["season"]

            league = g["league"]["name"]
            home = g["teams"]["home"]
            away = g["teams"]["away"]

            home_stats = fetch_team_stats(home["id"], league_id, season)
            away_stats = fetch_team_stats(away["id"], league_id, season)

            one_x_two, over_under, btts, chance = calculate_bets(home_stats, away_stats)

            games.append({
                "league": league,
                "match": f"{home['name']} vs {away['name']}",
                "chance": chance,
                "1X2": one_x_two,
                "OverUnder": over_under,
                "BTTS": btts
            })

        # Top 5 ehtimala görə
        games.sort(key=lambda x: x["chance"], reverse=True)
        return games[:5]

    except Exception as e:
        print("Error fetching games:", e)
        return []


# Telegram komandası /today
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        return

    await update.message.reply_text("📊 Real analiz edilir...\n⏳ Bir neçə saniyə gözlə")

    games = get_top_games()

    if not games:
        await update.message.reply_text("❌ Yaxın 24 saat üçün uyğun oyun tapılmadı")
        return

    msg = "⚽ Yaxın 24 saat üçün TOP 5 oyun:\n\n"
    for g in games:
        msg += (
            f"{g['league']}\n"
            f"{g['match']}\n"
            f"Ehtimal: {g['chance']}%\n"
            f"1X2: {g['1X2']} | Over/Under: {g['OverUnder']} | BTTS: {g['BTTS']}\n\n"
        )

    await update.message.reply_text(msg)


# Main
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("today", today))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
