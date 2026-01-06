import os
import aiohttp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import date

BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))
API_KEY = os.getenv("API_FOOTBALL_KEY")

# Helper: async GET
async def async_get(session, url):
    async with session.get(url) as response:
        return await response.json(), response.status

# Real data: fixtures, then statistics
async def fetch_fixtures():
    url = f"https://v3.football.api-sports.io/fixtures?date={date.today()}"
    headers = {"x-apisports-key": API_KEY}
    async with aiohttp.ClientSession(headers=headers) as session:
        data, status = await async_get(session, url)
        if status != 200:
            return None, status
        return data.get("response", []), 200

# Fetch head-to-head for team IDs
async def fetch_h2h(session, id1, id2):
    params = f"h2h={id1}-{id2}"
    url = f"https://v3.football.api-sports.io/fixtures/headtohead?{params}"
    data, status = await async_get(session, url)
    if status != 200:
        return []
    return data.get("response", [])

# Fetch last matches of a team
async def fetch_last_matches(session, team_id):
    url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&season={date.today().year}"
    data, status = await async_get(session, url)
    if status != 200:
        return []
    return data.get("response", [])

# Main command
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

    async with aiohttp.ClientSession(headers={"x-apisports-key": API_KEY}) as session:
        scored_games = []

        for g in fixtures:
            home = g["teams"]["home"]
            away = g["teams"]["away"]

            # Get past matches
            home_matches = await fetch_last_matches(session, home["id"])
            away_matches = await fetch_last_matches(session, away["id"])

            # Calculate simple form (last10 wins%)
            home_wins = sum(1 for m in home_matches[:10] if m["score"]["fulltime"]["home"] >
                             m["score"]["fulltime"]["away"])
            away_wins = sum(1 for m in away_matches[:10] if m["score"]["fulltime"]["away"] >
                             m["score"]["fulltime"]["home"])
            form_score = ((home_wins + away_wins) / 20) * 100

            # H2H
            h2h = await fetch_h2h(session, home["id"], away["id"])
            h2h_score = 0
            if h2h:
                h2h_score = sum(1 for x in h2h[:5] if x["teams"]["home"]["id"] == home["id"]) / len(h2h[:5]) * 100

            # Home advantage
            home_adv = 1 if home["id"] else 0

            probability = int((form_score + h2h_score + home_adv*10) / 3)

            # Odds filter from API (should be in fixture)
            odds = None
            if g.get("odds") and len(g["odds"]) > 0:
                bets = g["odds"][0]["bookmakers"]
                if bets:
                    best = bets[0]["bets"]
                    if best and len(best)>0:
                        odds_val = best[0]["values"][0]["value"]
                        if odds_val and odds_val >= 1.3:
                            odds = odds_val

            if odds:
                scored_games.append((probability, odds, g))

        if not scored_games:
            await update.message.reply_text("⚠️ Bu gün uyğun oyun tapılmadı.")
            return

        scored_games.sort(reverse=True, key=lambda x: x[0])
        top3 = scored_games[:3]

        text = "⚽ Bugünkü ən uğurlu 3 oyun:\n\n"
        for prob, odds_val, g2 in top3:
            text += (f"{g2['league']['name']}: {g2['teams']['home']['name']} vs "
                     f"{g2['teams']['away']['name']}\nEhtimal: {prob}% | Bet koeff: {odds_val}\n\n")

        await update.message.reply_text(text)

# Main
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("today", today))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
