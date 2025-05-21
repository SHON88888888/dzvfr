# bot.py
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
import os
from gpt_assistant import answer_question_with_context
from vector_store import init_vector_store

# === Загрузка переменных окружения ===
load_dotenv(dotenv_path="/opt/dzvfr/.env")
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# === Инициализация векторной базы ===
vector_store = init_vector_store()

# === Хранилище диалогов по chat_id ===
session_memory = {}

# === Команды ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Я — нейроконсультант по аудиторским отчётам. Задай любой вопрос, и я найду ответ по регламентам и отчётам."
    )

async def list_reports(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    docs = vector_store.similarity_search("проверка", k=200)
    seen = set()
    for doc in docs:
        src = doc.metadata.get("source", "").strip()
        if src:
            seen.add(src)
    if not seen:
        await update.message.reply_text("❌ Пока в базе нет ни одного отчёта.")
        return
    report_list = "\n".join(f"• {name}" for name in sorted(seen))
    await update.message.reply_text(f"📄 Отчёты в базе:\n{report_list}")

# === Ответ на любое сообщение ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = update.message.text
    chat_id = update.message.chat_id

    history = session_memory.get(chat_id, [])
    response = answer_question_with_context(user_input, vector_store, history)

    # Обновляем память
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": response})
    session_memory[chat_id] = history[-10:]  # ограничим память до 10 сообщений

    await update.message.reply_text(response)

# === Запуск приложения ===
app = ApplicationBuilder().token(TG_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reports", list_reports))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == '__main__':
    print("🚀 Бот запущен. Ждёт вопросы в Telegram...")
    app.run_polling()
