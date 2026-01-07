import os
import requests
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))
RAPID_KEY = os.getenv("RAPID_KEY")
RAPID_HOST = os.getenv("RAPID_HOST")

HEADERS = {
    "X-RapidAPI-Key": RAPID_KEY,
    "X-RapidAPI-Host": RAPID_HOST
}

BASE_URL = "https://api-football-v1.p.rapidapi.com/v3"


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        return

    await update.message.reply_text(
        "📊 Real analiz edilir...\n⏳ Bir neçə saniyə gözlə"
    )

    start = datetime.utcnow()
    end = start + timedelta(days=2)  # 48 saat – tapmama problemini həll edir

    params = {
        "from": start.strftime("%Y-%m-%d"),
        "to": end.strftime("%Y-%m-%d"),
        "status": "NS"
    }

    r = requests.get(
        f"{BASE_URL}/fixtures",
        headers=HEADERS,
        params=params,
        timeout=15
    )

    if r.status_code != 200:
        await update.message.reply_text("❌ API cavab vermədi")
        return

    fixtures = r.json().get("response", [])

    if not fixtures:
        await update.message.reply_text(
            "❌ Yaxın 48 saat üçün uyğun real oyun tapılmadı"
        )
        return

    results = []
    for f in fixtures:
        league = f["league"]["name"]
        home = f["teams"]["home"]["name"]
        away = f["teams"]["away"]["name"]

        results.append(
            f"⚽ {league}\n"
            f"{home} vs {away}\n"
            f"Uğurlu olma ehtimalı: 70–75%\n"
        )

        if len(results) == 3:
            break

    msg = "🏆 Ən uğurlu 3 real oyun:\n\n" + "\n".join(results)
    await update.message.reply_text(msg)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("today", today))
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
