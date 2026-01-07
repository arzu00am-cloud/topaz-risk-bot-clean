import os
import requests
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import asyncio

# =========================
# Environment variables
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID_STR = os.getenv("USER_ID")
API_KEY = os.getenv("API_FOOTBALL_KEY")

# Kontroller
if not all([BOT_TOKEN, USER_ID_STR, API_KEY]):
    raise ValueError("Missing environment variables")

USER_ID = int(USER_ID_STR)
HEADERS = {"x-apisports-key": API_KEY}
FIXTURES_URL = "https://v3.football.api-sports.io/fixtures"
STATS_URL = "https://v3.football.api-sports.io/teams/statistics"

# Cache için (aynı takım için tekrar tekrar istek yapmamak)
team_stats_cache = {}

def fetch_team_stats(team_id, league_id, season):
    """Cache'li takım istatistikleri"""
    cache_key = f"{team_id}_{league_id}_{season}"
    
    if cache_key in team_stats_cache:
        return team_stats_cache[cache_key]
    
    try:
        r = requests.get(STATS_URL, headers=HEADERS,
                         params={"team": team_id, "league": league_id, "season": season})
        if r.status_code != 200:
            stats = {"win_rate": 50, "avg_goals": 1.5, "draw_rate": 30}
            team_stats_cache[cache_key] = stats
            return stats
            
        data = r.json().get("response")
        if not data:
            stats = {"win_rate": 50, "avg_goals": 1.5, "draw_rate": 30}
            team_stats_cache[cache_key] = stats
            return stats

        played = data["fixtures"]["played"]["total"]
        wins = data["fixtures"]["wins"]["total"]
        draws = data["fixtures"]["draws"]["total"]
        goals = data["goals"]["for"]["total"]["total"]

        win_rate = int((wins / played) * 100) if played else 50
        draw_rate = int((draws / played) * 100) if played else 30
        avg_goals = goals / played if played else 1.5
        
        # Limit değerler
        win_rate = min(max(win_rate, 20), 85)
        draw_rate = min(max(draw_rate, 10), 50)
        
        stats = {"win_rate": win_rate, "avg_goals": avg_goals, "draw_rate": draw_rate}
        team_stats_cache[cache_key] = stats
        return stats
        
    except Exception as e:
        print(f"Error fetching stats: {e}")
        stats = {"win_rate": 50, "avg_goals": 1.5, "draw_rate": 30}
        team_stats_cache[cache_key] = stats
        return stats

def calculate_match_rating(home_stats, away_stats):
    """Daha iyi rating hesaplama"""
    hw = home_stats["win_rate"]
    aw = away_stats["win_rate"]
    hg = home_stats["avg_goals"]
    ag = away_stats["avg_goals"]
    
    # Formül: (win_rate * 0.5) + (avg_goals * 20 * 0.3) + (draw_probability * 0.2)
    draw_prob = min(home_stats["draw_rate"], away_stats["draw_rate"])
    
    rating = (max(hw, aw) * 0.5) + ((hg + ag) * 20 * 0.3) + (draw_prob * 0.2)
    return min(rating, 100)

def calculate_bets(home_stats, away_stats):
    """Geliştirilmiş tahmin algoritması"""
    hw = home_stats["win_rate"]
    aw = away_stats["win_rate"]
    hg = home_stats["avg_goals"]
    ag = away_stats["avg_goals"]
    
    # 1X2 (daha akıllı)
    if hw > aw + 15:
        one_x_two = "1"
    elif aw > hw + 15:
        one_x_two = "2"
    elif abs(hw - aw) < 10:
        one_x_two = "X"
    else:
        one_x_two = "1" if hw > aw else "2"
    
    # Over/Under 2.5
    total_goals = hg + ag
    if total_goals > 3.0:
        over_under = "Over 2.5"
    elif total_goals < 2.0:
        over_under = "Under 2.5"
    else:
        over_under = "Over 2.5" if total_goals >= 2.5 else "Under 2.5"
    
    # BTTS (Both Teams to Score)
    btts_prob = min(hg, ag) * 30  # Basit bir olasılık
    btts = "Yes" if btts_prob > 50 else "No"
    
    return one_x_two, over_under, btts

async def get_top_games():
    """Asenkron şekilde maçları getir"""
    now = datetime.utcnow()
    start_date = now.strftime("%Y-%m-%d")
    end_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    
    params = {"from": start_date, "to": end_date, "status": "NS"}
    
    try:
        r = requests.get(FIXTURES_URL, headers=HEADERS, params=params, timeout=10)
        if r.status_code != 200:
            print(f"API error: {r.status_code}")
            return []
        
        data = r.json().get("response", [])
        games = []
        
        for g in data[:20]:  # İlk 20 maçla sınırla
            league_id = g["league"]["id"]
            season = g["league"]["season"]
            
            home_team = g["teams"]["home"]
            away_team = g["teams"]["away"]
            
            # Asenkron olarak istatistikleri al
            home_stats = fetch_team_stats(home_team["id"], league_id, season)
            away_stats = fetch_team_stats(away_team["id"], league_id, season)
            
            rating = calculate_match_rating(home_stats, away_stats)
            one_x_two, over_under, btts = calculate_bets(home_stats, away_stats)
            
            games.append({
                "league": g["league"]["name"],
                "match": f"{home_team['name']} vs {away_team['name']}",
                "time": g["fixture"]["date"][11:16] if "date" in g["fixture"] else "N/A",
                "rating": round(rating, 1),
                "1X2": one_x_two,
                "OverUnder": over_under,
                "BTTS": btts
            })
        
        # Rating'e göre sırala
        games.sort(key=lambda x: x["rating"], reverse=True)
        return games[:5]
        
    except Exception as e:
        print(f"Error: {e}")
        return []

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Güncellenmiş komut handler"""
    if update.effective_user.id != USER_ID:
        await update.message.reply_text("⚠️ Yetkiniz yok.")
        return
    
    processing_msg = await update.message.reply_text(
        "📊 Maçlar analiz ediliyor...\n⏳ Lütfen bekleyin (10-15 saniye)"
    )
    
    games = await get_top_games()
    
    await processing_msg.delete()  # İşlem mesajını sil
    
    if not games:
        await update.message.reply_text("❌ Bugün için uygun maç bulunamadı")
        return
    
    msg = "⚽ Önerilen 5 Maç:\n\n"
    for i, g in enumerate(games, 1):
        msg += (
            f"🏆 {g['league']}\n"
            f"🕒 {g['time']} | ⭐ {g['rating']}/100\n"
            f"🤼 {g['match']}\n"
            f"🎯 1X2: {g['1X2']} | Gol: {g['OverUnder']} | BTTS: {g['BTTS']}\n"
            f"{'─' * 30}\n"
        )
    
    msg += "\n⚠️ Not: Bu sadece tahmindir. Lütfen sorumlu bahis yapın."
    await update.message.reply_text(msg)

def main():
    """Ana fonksiyon"""
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("start", lambda u,c: u.message.reply_text("Bugünkü maçlar için /today yazın")))
    
    print("🤖 Bot başlatılıyor...")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
