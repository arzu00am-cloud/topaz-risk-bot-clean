import os
import requests
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import json

# =========================
# Environment variables
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID_STR = os.getenv("USER_ID")
API_KEY = os.getenv("API_FOOTBALL_KEY")

# Kontroller
if not BOT_TOKEN:
    print("❌ BOT_TOKEN eksik!")
    exit()
if not USER_ID_STR:
    print("❌ USER_ID eksik!")
    exit()
if not API_KEY:
    print("❌ API_FOOTBALL_KEY eksik!")
    exit()

USER_ID = int(USER_ID_STR)
HEADERS = {"x-apisports-key": API_KEY}
FIXTURES_URL = "https://v3.football.api-sports.io/fixtures"
STATS_URL = "https://v3.football.api-sports.io/teams/statistics"

def debug_print(*args):
    """Debug mesajları için"""
    print(f"[DEBUG] {datetime.now().strftime('%H:%M:%S')}:", *args)

def get_current_season():
    """Avtomatik mövsüm hesablanması"""
    now = datetime.now()
    current_year = now.year
    current_month = now.month
    
    if current_month >= 8:  # Avqust və sonrası
        return current_year
    else:
        return current_year - 1

def fetch_team_stats(team_id, league_id, season):
    """Takım istatistiklerini al"""
    cache_key = f"{team_id}_{league_id}_{season}"
    
    try:
        params = {"team": team_id, "league": league_id, "season": season}
        r = requests.get(STATS_URL, headers=HEADERS, params=params, timeout=10)
        
        if r.status_code != 200:
            debug_print(f"Stats API hatası: {r.status_code}")
            return {"win_rate": 50, "avg_goals": 1.5, "draw_rate": 30}
        
        data = r.json()
        
        if "errors" in data and data["errors"]:
            return {"win_rate": 50, "avg_goals": 1.5, "draw_rate": 30}
            
        response = data.get("response")
        if not response:
            return {"win_rate": 50, "avg_goals": 1.5, "draw_rate": 30}
            
        played = response.get("fixtures", {}).get("played", {}).get("total", 0)
        wins = response.get("fixtures", {}).get("wins", {}).get("total", 0)
        draws = response.get("fixtures", {}).get("draws", {}).get("total", 0)
        goals = response.get("goals", {}).get("for", {}).get("total", {}).get("total", 0)
        
        if played == 0:
            return {"win_rate": 50, "avg_goals": 1.5, "draw_rate": 30}
        
        win_rate = int((wins / played) * 100) if played else 50
        draw_rate = int((draws / played) * 100) if played else 30
        avg_goals = goals / played if played else 1.5
        
        win_rate = min(max(win_rate, 20), 85)
        draw_rate = min(max(draw_rate, 10), 50)
        
        return {"win_rate": win_rate, "avg_goals": avg_goals, "draw_rate": draw_rate}
        
    except Exception as e:
        debug_print(f"fetch_team_stats hatası: {e}")
        return {"win_rate": 50, "avg_goals": 1.5, "draw_rate": 30}

def get_top_games():
    """Bugünkü maçları getir"""
    now = datetime.utcnow()
    start_date = now.strftime("%Y-%m-%d")
    end_date = (now + timedelta(days=2)).strftime("%Y-%m-%d")
    current_season = get_current_season()  # ƏLAVƏ EDİLDİ
    
    debug_print(f"Tarih aralığı: {start_date} - {end_date}, Mövsüm: {current_season}")
    
    params = {
        "from": start_date,
        "to": end_date,
        "status": "NS",
        "timezone": "Europe/Istanbul",
        "season": current_season  # ƏLAVƏ EDİLDİ
    }
    
    try:
        debug_print("API isteği yapılıyor...")
        r = requests.get(FIXTURES_URL, headers=HEADERS, params=params, timeout=15)
        
        debug_print(f"API Response Status: {r.status_code}")
        
        if r.status_code != 200:
            debug_print(f"API Error: {r.text}")
            return []
        
        data = r.json()
        
        if "errors" in data and data["errors"]:
            debug_print(f"API Errors: {data['errors']}")
            return []
        
        fixtures = data.get("response", [])
        debug_print(f"Toplam {len(fixtures)} maç bulundu")
        
        if not fixtures:
            return []
        
        games = []
        
        for i, fixture in enumerate(fixtures[:15]):
            try:
                league_info = fixture.get("league", {})
                teams = fixture.get("teams", {})
                
                if not league_info or not teams:
                    continue
                
                league_id = league_info.get("id")
                season = league_info.get("season")
                league_name = league_info.get("name", "Bilinmeyen Lig")
                
                home_team = teams.get("home", {})
                away_team = teams.get("away", {})
                
                if not home_team.get("id") or not away_team.get("id"):
                    continue
                
                home_name = home_team.get("name", "Ev Sahibi")
                away_name = away_team.get("name", "Deplasman")
                
                debug_print(f"Maç {i+1}: {home_name} vs {away_name}")
                
                home_stats = fetch_team_stats(home_team["id"], league_id, season)
                away_stats = fetch_team_stats(away_team["id"], league_id, season)
                
                hw = home_stats["win_rate"]
                aw = away_stats["win_rate"]
                hg = home_stats["avg_goals"]
                ag = away_stats["avg_goals"]
                
                rating = (max(hw, aw) * 0.5) + ((hg + ag) * 15)
                
                if hw > aw + 10:
                    one_x_two = "1"
                elif aw > hw + 10:
                    one_x_two = "2"
                elif abs(hw - aw) < 5:
                    one_x_two = "X"
                else:
                    one_x_two = "1" if hw > aw else "2"
                
                total_goals = hg + ag
                over_under = "Over 2.5" if total_goals >= 2.5 else "Under 2.5"
                
                btts = "Yes" if (hg > 0.8 and ag > 0.8) else "No"
                
                games.append({
                    "league": league_name,
                    "match": f"{home_name} vs {away_name}",
                    "rating": round(rating, 1),
                    "1X2": one_x_two,
                    "OverUnder": over_under,
                    "BTTS": btts,
                    "home_win": hw,
                    "away_win": aw,
                    "total_goals": round(total_goals, 2)
                })
                
            except Exception as e:
                debug_print(f"Maç işleme hatası: {e}")
                continue
        
        if games:
            games.sort(key=lambda x: x["rating"], reverse=True)
            debug_print(f"{len(games)} maç işlendi, top {min(5, len(games))} gösterilecek")
            return games[:5]
        else:
            return []
            
    except requests.exceptions.Timeout:
        debug_print("API timeout hatası")
        return []
    except Exception as e:
        debug_print(f"get_top_games hatası: {e}")
        return []

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bugünkü maçları göster"""
    try:
        user_id = update.effective_user.id
        
        if user_id != USER_ID:
            await update.message.reply_text("⚠️ Bu botu kullanma yetkiniz yok.")
            return
        
        await update.message.reply_text(
            "📊 Maçlar analiz ediliyor...\n"
            "⏳ Bu işlem 15-20 saniye sürebilir..."
        )
        
        games = get_top_games()
        debug_print(f"get_top_games sonucu: {len(games)} maç")
        
        if not games:
            debug_msg = (
                "❌ Bugün için uygun maç bulunamadı.\n\n"
                "Olası nedenler:\n"
                "• API limiti dolmuş olabilir\n"
                "• Bugün maç olmayabilir\n"
                "• API anahtarı geçersiz\n\n"
                "/test komutu ile API durumunu kontrol edin."
            )
            await update.message.reply_text(debug_msg)
            return
        
        msg = "⚽ Bugünün Önerilen Maçları ⚽\n\n"
        
        for i, game in enumerate(games, 1):
            msg += (
                f"{i}. {game['league']}\n"
                f"🤼 {game['match']}\n"
                f"⭐ Puan: {game['rating']}/100\n"
                f"📊 İstatistik: Ev %{game['home_win']} - %{game['away_win']} Deplasman | Toplam Gol: {game['total_goals']}\n"
                f"🎯 Tahminler:\n"
                f"• 1X2: {game['1X2']}\n"
                f"• Gol Sayısı: {game['OverUnder']}\n"
                f"• Her İki Takım Gol: {game['BTTS']}\n"
                f"────────────────────\n\n"
            )
        
        msg += (
            "⚠️ Önemli Not:\n"
            "• Bu tahminler bilgilendirme amaçlıdır\n"
            "• Kesin sonuç garantisi yoktur\n"
            "• Sorumlu bahis yapınız"
        )
        
        await update.message.reply_text(msg)
        
    except Exception as e:
        debug_print(f"today komutu hatası: {e}")
        await update.message.reply_text("❌ Bir hata oluştu. Lütfen daha sonra tekrar deneyin.")

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test komutu - API bağlantısını kontrol et"""
    if update.effective_user.id != USER_ID:
        await update.message.reply_text("⚠️ Bu botu kullanma yetkiniz yok.")
        return
    
    debug_print("Test komutu çalıştı")
    
    # AVTOMATİK mövsüm hesablanması
    season = get_current_season()  # YENİ FUNKSİYA İSTİFADƏ EDİLDİ
    
    test_params = {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "league": 39,  # Premier League
        "season": season  # ƏLAVƏ EDİLDİ
    }
    
    try:
        r = requests.get(FIXTURES_URL, headers=HEADERS, params=test_params, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            if "errors" in data and data["errors"]:
                api_status = f"❌ API Error: {data['errors']}"
            else:
                matches_found = len(data.get("response", []))
                api_status = f"✅ API Bağlantısı Çalışıyor. {matches_found} maç bulundu."
        elif r.status_code == 429:
            api_status = "❌ API Limiti Aşıldı"
        elif r.status_code == 403:
            api_status = "❌ API Anahtarı Geçersiz"
        else:
            api_status = f"❌ API Error: Status Code {r.status_code}"
        
        response_text = (
            f"🔍 API Test Sonucu\n\n"
            f"• Status Code: {r.status_code}\n"
            f"• API Durumu: {api_status}\n"
            f"• Təyin edilmiş Mövsüm: {season}\n"
            f"• Bot Token: {'✅ Mövcud' if BOT_TOKEN else '❌ Eksik'}\n"
            f"• USER_ID: {'✅ ' + str(USER_ID) if USER_ID_STR else '❌ Eksik'}\n"
            f"• Zaman: {datetime.now().strftime('%H:%M:%S')}\n\n"
            f"API Key ilk 10 karakter: {API_KEY[:10] if API_KEY else 'EKSİK'}..."
        )
        
        await update.message.reply_text(response_text)
        
    except requests.exceptions.Timeout:
        await update.message.reply_text("❌ API Timeout - API'ye bağlanılamıyor")
    except requests.exceptions.ConnectionError:
        await update.message.reply_text("❌ Bağlantı Hatası - İnternet bağlantısı yok")
    except Exception as e:
        await update.message.reply_text(f"❌ Test hatası: {str(e)}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Başlangıç komutu"""
    welcome_msg = (
        "🤖 Futbol Tahmin Botu\n\n"
        "Komutlar:\n"
        "• /start - Bu mesajı göster\n"
        "• /today - Bugünün önerilen maçlarını göster\n"
        "• /test - API bağlantı testi\n\n"
        "⚠️ Sadece yetkili kullanıcılar komutları kullanabilir."
    )
    await update.message.reply_text(welcome_msg)

def main():
    """Ana fonksiyon"""
    debug_print("Bot başlatılıyor...")
    debug_print(f"USER_ID: {USER_ID}")
    debug_print(f"API Key ilk 10 karakter: {API_KEY[:10]}...")
    
    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("today", today))
        app.add_handler(CommandHandler("test", test))
        
        debug_print("🤖 Bot başarıyla başlatıldı!")
        print("Bot çalışıyor... Ctrl+C ile durdurabilirsiniz.")
        
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            poll_interval=1.0
        )
        
    except Exception as e:
        debug_print(f"Bot başlatma hatası: {e}")
        import traceback
        debug_print(traceback.format_exc())

if __name__ == "__main__":
    main()
