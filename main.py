import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ====================================
# 1️⃣ Mühit dəyişənlərini oxuyuruq
# ====================================
BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID_ENV = os.getenv("USER_ID")

if BOT_TOKEN is None:
    raise Exception("BOT_TOKEN mühit dəyişəni əlavə edilməyib!")
if USER_ID_ENV is None:
    raise Exception("USER_ID mühit dəyişəni əlavə edilməyib!")

USER_ID = int(USER_ID_ENV)

# ====================================
# 2️⃣ /today komandası
# ====================================
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Yalnız sizin ID-nizə cavab versin
    if update.effective_user.id != USER_ID:
        return
    
    # Burada sonradan risk logic əlavə ediləcək
    await update.message.reply_text(
        "📊 Analiz edilir...\n⏳ Bir neçə saniyə gözlə"
    )

# ====================================
# 3️⃣ Botu işə salmaq
# ====================================
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("today", today))

    print("✅ Bot polling started")  # Logs-da görünəcək
    await app.run_polling()

# ====================================
# 4️⃣ Main entry
# ====================================
if __name__ == "__main__":
    asyncio.run(main())
