import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 Sora 2", callback_data="sora")],
        [InlineKeyboardButton("📸 Видео из фото", callback_data="photo_video")],
        [InlineKeyboardButton("ℹ️ Как это работает", callback_data="info")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "✨ MySora AI\\n\\nВыбери режим. Видео создаётся вручную оператором в Google Flow.",
        reply_markup=menu()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "info":
        await q.message.reply_text("Отправь фото, затем описание видео. Оператор создаст видео и пришлёт его сюда.")
    elif q.data in ("sora", "photo_video"):
        context.user_data["waiting_photo"] = True
        context.user_data["mode"] = "Sora 2"
        await q.message.reply_text("📷 Пришли фотографию, из которой сделать видео.")

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_photo"):
        await update.message.reply_text("Сначала нажми кнопку «Sora 2» в меню /start.")
        return
    context.user_data["photo"] = update.message.photo[-1].file_id
    context.user_data["waiting_photo"] = False
    context.user_data["waiting_prompt"] = True
    await update.message.reply_text("✍️ Теперь напиши промпт: что должно происходить в видео.")

async def prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("waiting_prompt"):
        await update.message.reply_text("Чтобы создать заявку, нажми /start и выбери Sora 2.")
        return
    text = update.message.text
    uid = update.effective_user.id
    user = update.effective_user
    photo_id = context.user_data.get("photo")
    caption = (
        f"🆕 Заявка MySora AI\\n"
        f"👤 {user.full_name}\\n"
        f"🆔 USER_ID: {uid}\\n"
        f"🎞 Модель: Sora 2\\n"
        f"📝 Промпт: {text}\\n\\n"
        f"Чтобы выдать видео: /deliver {uid}, затем отправь видео."
    )
    if ADMIN_ID:
        if photo_id:
            await context.bot.send_photo(ADMIN_ID, photo_id, caption=caption)
        else:
            await context.bot.send_message(ADMIN_ID, caption)
    context.user_data.clear()
    await update.message.reply_text(
        "✅ Заявка отправлена оператору!\\n"
        "Когда видео будет готово, оно придёт сюда.\\n\\n"
        "Новая заявка: /start"
    )

async def deliver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Формат: /deliver USER_ID")
        return
    target = int(context.args[0])
    context.user_data["deliver_to"] = target
    await update.message.reply_text(f"Ок! Теперь отправь видео сообщением — оно уйдёт пользователю {target}.")

async def admin_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    target = context.user_data.get("deliver_to")
    if not target:
        await update.message.reply_text("Сначала напиши /deliver USER_ID")
        return
    video = update.message.video
    await context.bot.send_video(target, video.file_id, caption="🎬 MySora AI — твоё видео готово!")
    context.user_data.pop("deliver_to", None)
    await update.message.reply_text("✅ Видео отправлено клиенту!")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Заявка отменена. /start — начать заново.")

def main():
    if not TOKEN:
        raise RuntimeError("Добавь BOT_TOKEN в Railway Variables")
    if not ADMIN_ID:
        raise RuntimeError("Добавь ADMIN_ID в Railway Variables")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("deliver", deliver))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, prompt))
    app.add_handler(MessageHandler(filters.VIDEO, admin_video))
    app.run_polling()

if __name__ == "__main__":
    main()
