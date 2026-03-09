import os
import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler

# Твой токен (мы его спрячем в настройки Vercel)
TOKEN = os.getenv("TELEGRAM_TOKEN")

async def start(update, context):
    chat_id = update.effective_chat.id
    
    # 1. Текст сообщения
    text = (
        "**BND Delivery Phuket 🌴**\n\n"
        "Напишите нам в чат, мы ответим максимально быстро!\n"
        "Используйте кнопки ниже для заказа:"
    )
    
    # 2. Твои кнопки-плитки (шахматка)
    keyboard = [
        [
            InlineKeyboardButton("🥥 Каталог", url="https://bndeliveryphuket.click/info"),
            InlineKeyboardButton("👤 Оператор", url="https://bndeliveryphuket.click/chat")
        ],
        [
            InlineKeyboardButton("📸 Instagram", url="https://bndeliveryphuket.click/insta"),
            InlineKeyboardButton("🟢 WhatsApp", url="https://bndeliveryphuket.click/wa")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # 3. Отправка сообщения
    message = await context.bot.send_message(
        chat_id=chat_id, 
        text=text, 
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    # 4. АВТО-ЗАКРЕП (Магия)
    await context.bot.pin_chat_message(chat_id=chat_id, message_id=message.message_id)

# Это нужно для Vercel, чтобы он понимал, как запускать бота
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))

# Для Vercel Serverless (упрощенно)
async def handler(event, context):
    return await app.initialize()
