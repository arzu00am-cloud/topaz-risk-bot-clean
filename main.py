import os
import requests
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# 1. RAILWAY ENVIRONMENT VARIABLES
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID_STR = os.getenv("USER_ID")
SPORTMONKS_API_KEY = os.getenv("API_KEY")  # Sportmonks açarı

if not BOT_TOKEN:
    print("❌ BOT_TOKEN təyin edilməyib!")
    exit()
if not USER_ID_STR:
    print("❌ USER_ID təyin edilməyib!")
    exit()
if not SPORTMONKS_API_KEY:
    print("❌ API_KEY (Sportmonks Açarı) təyin edilməyib!")
    exit()

USER_ID = int(USER_ID_STR)

# =========================
# 2. SPORTMONKS API KONFİQURASİYASI
# =========================
SPORTMONKS_BASE_URL = "https://api.sportmonks.com/v3/football"
FIXTURES_URL = f"{SPORTMONKS_BASE_URL}/fixtures"
HEADERS = {
    "Authorization": f"Bearer {SPORTMONKS_API_KEY}"
}

def debug_print(*args):
    print(f"[DEBUG] {datetime.now().strftime('%H:%M:%S')}:", *args)

def get_top_games():
    """Sportmonks API-dən BÜTÜN gələcək oyunları gətirir (vaxt məhdudiyyətisiz)."""
    
    # ✅ ƏSAS DƏYİŞİKLİK: VAXT FİLTRİ SİLİNDİ
    # İndi API-dən sadəcə gələcək oyunları soruşuruq
    params = {
        "include": "participants;league",  # Komanda və liqa məlumatları
        "filters[status][eq]": "NS",      # Yalnız "Not Started" (başlamamış) oyunlar
        "per_page": 30,                   # Daha çox oyun götürək
        "sort": "starting_at"             # Başlama vaxtına görə sırala
    }
    
    try:
        debug_print(f"Sportmonks API sorğusu (vaxt məhdudiyyətisiz)...")
        
        response = requests.get(FIXTURES_URL, headers=HEADERS, params=params, timeout=15)
        debug_print(f"API Status: {response.status_code}")
        
        if response.status_code != 200:
            debug_print(f"API səhvi: {response.text[:200]}")
            return []
        
        data = response.json()
        fixtures = data.get("data", [])
        
        if not fixtures:
            debug_print("Heç bir gələcək oyun tapılmadı.")
            return []
        
        debug_print(f"Ümumi {len(fixtures)} gələcək oyun tapıldı")
        
        games = []
        for fixture in fixtures:
            try:
                # Liqa məlumatları
                league = fixture.get("league", {})
                league_name = league.get("name", "N/A")
                league_id = league.get("id", 0)
                
                # Komanda məlumatları
                participants = fixture.get("participants", [])
                home_team = next((p for p in participants if p.get("meta", {}).get("location") == "home"), {})
                away_team = next((p for p in participants if p.get("meta", {}).get("location") == "away"), {})
                
                home_name = home_team.get("name", "Ev Sahibi")
                away_name = away_team.get("name", "Səfər")
                match_name = f"{home_name} vs {away_name}"
                
                # Başlama vaxtı
                start_time = fixture.get("starting_at", "")
                if start_time:
                    try:
                        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        time_display = start_dt.strftime("%d.%m %H:%M")  # Gün.Ay Saat:Dəqiqə formatında
                        days_until = (start_dt.date() - datetime.now().date()).days
                    except:
                        time_display = start_time[5:16] if len(start_time) > 16 else start_time
                        days_until = 0
                else:
                    time_display = "Təyin edilməyib"
                    days_until = 0
                
                # REYTİNQ HESABLANMASI (nümunə - öz məntiqinizlə dəyişin)
                base_rating = 40
                
                # Məşhur liqalara daha yüksək reytinq
                popular_leagues = ["Premier League", "La Liga", "Bundesliga", "Serie A", "Champions League"]
                if any(league in league_name for league in popular_leagues):
                    base_rating += 25
                
                # Tez başlayacaq oyunlara daha yüksək reytinq
                if days_until <= 7:
                    base_rating += min(20, 25 - days_until * 3)
                
                games.append({
                    "league": league_name,
                    "match": match_name,
                    "time": time_display,
                    "rating": min(base_rating, 95),
                    "home": home_name,
                    "away": away_name,
                    "days_until": days_until
                })
                
            except Exception as e:
                debug_print(f"Oyun emal səhvi: {e}")
                continue
        
        # Reytinqə görə sırala və ilk 8-i götür (çünki daha çox oyun var)
        games.sort(key=lambda x: x["rating"], reverse=True)
        return games[:8]  # 8 oyun göstər
        
    except requests.exceptions.Timeout:
        debug_print("API sorğusu zaman aşımına uğradı")
        return []
    except Exception as e:
        debug_print(f"Ümumi xəta: {e}")
        return []

# =========================
# 3. TELEGRAM BOT KOMANDALARI
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        return
    await update.message.reply_text(
        "🤖 Futbol Proqnoz Botu (Vaxt Məhdudiyyətisiz)\n"
        "Əmrlər:\n"
        "/start - Bu mesaj\n"
        "/matches - Bütün gələcək oyunlar\n\n"
        "⚠️ Diqqət: Bu test versiyasıdır."
    )

async def matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        return
    
    await update.message.reply_text("🔍 Bütün gələcək oyunlar gətirilir...")
    
    games = get_top_games()
    
    if not games:
        await update.message.reply_text(
            "❌ Heç bir gələcək oyun tapılmadı.\n"
            "Ola bilər ki:\n"
            "• Pulsuz plan bu liqaları əhatə etmir\n"
            "• API-də heç bir planlaşdırılmış oyun yoxdur\n"
            "• API açarı düzgün deyil"
        )
        return
    
    # Oyunları günlərə görə qruplaşdır
    games_by_day = {}
    for game in games:
        day_key = game['time'].split()[0] if ' ' in game['time'] else 'Digər'
        if day_key not in games_by_day:
            games_by_day[day_key] = []
        games_by_day[day_key].append(game)
    
    message = "⚽ GƏLƏCƏK OYUNLAR (Reytinqə görə sıralanıb):\n\n"
    
    for day, day_games in games_by_day.items():
        message += f"📅 **{day}**\n"
        for i, game in enumerate(day_games, 1):
            message += (
                f"  {i}. {game['league']}\n"
                f"     🕒 {game['time']} | ⭐ {game['rating']}%\n"
                f"     🤼 {game['match']}\n"
            )
        message += "  ─────────────────\n"
    
    message += (
        f"\n📊 **Ümumi:** {len(games)} oyun tapıldı\n"
        "⚠️ **Xəbərdarlıq:** Bu reytinq sadəcə nümunədir.\n"
        "Həqiqi proqnoz üçün statistikalar lazımdır."
    )
    
    # Telegram mesaj limiti (4096 simvol) üçün kəsim
    if len(message) > 4000:
        message = message[:3900] + "\n[...mesaj qısaldıldı]"
    
    await update.message.reply_text(message, parse_mode='Markdown')

# =========================
# 4. BOTU BAŞLAT
# =========================
def main():
    debug_print("=" * 50)
    debug_print("Bot başladılır (Vaxt Məhdudiyyətisiz)...")
    debug_print(f"USER_ID: {USER_ID}")
    debug_print(f"API_KEY ilk 10 simvol: {SPORTMONKS_API_KEY[:10]}...")
    
    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("matches", matches))  # Əmr adı dəyişdi: /today -> /matches
        
        debug_print("✅ Bot uğurla başladıldı!")
        debug_print("Komanda: /matches")
        debug_print("=" * 50)
        
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        debug_print(f"❌ Bot başlatma xətası: {e}")

if __name__ == "__main__":
    main()
