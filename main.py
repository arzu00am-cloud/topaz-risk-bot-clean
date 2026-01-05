import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        return
    await update.message.reply_text(
        "📊 Analiz edilir...\n⏳ Bir neçə saniyə gözlə"
    )

async def main():
    # ApplicationBuilder tam async və Updater-i gizlədir
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Komandaları əlavə edin
    app.add_handler(CommandHandler("today", today))
    
    print("✅ Bot polling started")
    # Async polling
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
