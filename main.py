import os
import requests
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import json

# =========================
# Railway Environment Variables
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID_STR = os.getenv("USER_ID")
API_KEY = os.getenv("API_KEY")  # ⬅️ İndi bu, RapidAPI-dən aldığınız açar

if not BOT_TOKEN:
    print("❌ BOT_TOKEN təyin edilməyib!")
    exit()
if not USER_ID_STR:
    print("❌ USER_ID təyin edilməyib!")
    exit()
if not API_KEY:
    print("❌ API_KEY (RapidAPI Açarı) təyin edilməyib!")
    exit()

USER_ID = int(USER_ID_STR)

# =========================
# RapidAPI vasitəsilə API-Football Konfiqurasiyası
# =========================
HEADERS = {
    "x-rapidapi-key": API_KEY,        # RapidAPI açarı
    "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
}
# RapidAPI endpoint ünvanları
FIXTURES_URL = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
STATS_URL = "https://api-football-v1.p.rapidapi.com/v3/teams/statistics"

# =========================
# Köməkçi Funksiyalar
# =========================
def debug_print(*args):
    print(f"[DEBUG] {datetime.now().strftime('%H:%M:%S')}:", *args)

def get_current_season():
    """
    Cari futbol mövsümünü qaytarır.
    QEYD: Əgər RapidAPI planınız 2025 mövsümünə icazə verirsə,
    birbaşa 2025 qaytara bilərsiniz. Məsələn: return 2025
    """
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    # Futbol mövsümü adətən Avqustdan başlayır
    season = current_year if current_month >= 8 else current_year - 1
    
    # ⚠️ BURANI YOXLAYIN: Əgər testləriniz 2025 üçün işləyirsə, aşağıdakı sətri aktivləşdirin.
    # season = 2025
    debug_print(f"Hesablanmış mövsüm: {season}")
    return season

def fetch_team_stats(team_id, league_id, season):
    """Komanda statistikasını RapidAPI-dən alır."""
    try:
        params = {"team": team_id, "league": league_id, "season": season}
        r = requests.get(STATS_URL, headers=HEADERS, params=params, timeout=10)
        if r.status_code != 200:
            debug_print(f"Stats API səhvi: {r.status_code}")
            return {"win_rate": 50, "avg_goals": 1.5}
        data = r.json()
        if not data.get("response"):
            return {"win_rate": 50, "avg_goals": 1.5}
        resp = data["response"]
        played = resp["fixtures"]["played"]["total"]
        wins = resp["fixtures"]["wins"]["total"]
        goals = resp["goals"]["for"]["total"]["total"]
        win_rate = int((wins / played) * 100) if played else 50
        avg_goals = goals / played if played else 1.5
        return {"win_rate": win_rate, "avg_goals": avg_goals}
    except Exception as e:
        debug_print(f"fetch_team_stats səhvi: {e}")
        return {"win_rate": 50, "avg_goals": 1.5}

def calculate_bets(home_stats, away_stats):
    """Proqnozları hesablayır."""
    hw, aw = home_stats["win_rate"], away_stats["win_rate"]
    if hw > aw + 15:
        one_x_two = "1"
    elif aw > hw + 15:
        one_x_two = "2"
    elif abs(hw - aw) < 10:
        one_x_two = "X"
    else:
        one_x_two = "1" if hw > aw else "2"
    total_goals = home_stats["avg_goals"] + away_stats["avg_goals"]
    over_under = "Over 2.5" if total_goals >= 2.5 else "Under 2.5"
    btts = "Yes" if home_stats["avg_goals"] > 0.8 and away_stats["avg_goals"] > 0.8 else "No"
    chance = max(hw, aw)
    return one_x_two, over_under, btts, chance

def get_top_games():
    """Günün top oyunlarını RapidAPI-dən alır."""
    now = datetime.utcnow()
    start_date = now.strftime("%Y-%m-%d")
    end_date = (now + timedelta(days=2)).strftime("%Y-%m-%d")
    season = get_current_season()  # Cari mövsüm
    
    params = {
        "from": start_date,
        "to": end_date,
        "status": "NS",
        "season": season  # ⬅️ Mövsüm parametri əlavə edildi
    }
    try:
        debug_print("RapidAPI sorğusu göndərilir...")
        r = requests.get(FIXTURES_URL, headers=HEADERS, params=params, timeout=15)
        debug_print(f"API Cavab Statusu: {r.status_code}")
        if r.status_code != 200:
            return []
        data = r.json()
        if "errors" in data and data["errors"]:
            debug_print(f"API Səhvləri: {data['errors']}")
            return []
        fixtures = data.get("response", [])
        debug_print(f"Toplam {len(fixtures)} oyun tapıldı")
        games = []
        for g in fixtures[:10]:  # İlk 10 oyunu işlə
            league = g["league"]
            league_id = league["id"]
            season = league["season"]
            home = g["teams"]["home"]
            away = g["teams"]["away"]
            home_stats = fetch_team_stats(home["id"], league_id, season)
            away_stats = fetch_team_stats(away["id"], league_id, season)
            one_x_two, over_under, btts, chance = calculate_bets(home_stats, away_stats)
            games.append({
                "league": league["name"],
                "match": f"{home['name']} vs {away['name']}",
                "chance": chance,
                "1X2": one_x_two,
                "OverUnder": over_under,
                "BTTS": btts
            })
        games.sort(key=lambda x: x["chance"], reverse=True)
        return games[:5]
    except Exception as e:
        debug_print(f"get_top_games səhvi: {e}")
        return []

# =========================
# Telegram Bot Komandaları
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot işləyir! /today yazaraq bugünkü oyunları görə bilərsiniz.")

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        return
    await update.message.reply_text("📊 Oyunlar təhlil edilir...")
    games = get_top_games()
    if not games:
        await update.message.reply_text("❌ Bu gün üçün oyun tapılmadı.")
        return
    msg = "⚽ Bugünün Top 5 Oyunu:\n\n"
    for g in games:
        msg += f"{g['league']}\n{g['match']}\nEhtimal: {g['chance']}%\n1X2: {g['1X2']} | Qol: {g['OverUnder']} | Hər iki komanda qol vurarmı: {g['BTTS']}\n\n"
    await update.message.reply_text(msg)

# =========================
# Əsas Proqram
# =========================
def main():
    debug_print("Bot başladılır...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))
    debug_print("Bot uğurla başladıldı!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
