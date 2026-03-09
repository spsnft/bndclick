import os
import asyncio
import json
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application

TOKEN = os.getenv("TELEGRAM_TOKEN")

async def handle_start(bot, chat_id):
    text = "BND Delivery Phuket 🌴\n\nНапишите нам, мы ответим быстро!"
    keyboard = [
        [InlineKeyboardButton("🥥 Каталог", url="https://bndeliveryphuket.click/info"),
         InlineKeyboardButton("👤 Оператор", url="https://bndeliveryphuket.click/chat")],
        [InlineKeyboardButton("📸 Instagram", url="https://bndeliveryphuket.click/insta"),
         InlineKeyboardButton("🟢 WhatsApp", url="https://bndeliveryphuket.click/wa")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем и сразу закрепляем
    msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
    await bot.pin_chat_message(chat_id=chat_id, message_id=msg.message_id)

async def handler(request):
    if request.method == "POST":
        bot = Bot(token=TOKEN)
        data = json.loads(request.body)
        update = Update.de_json(data, bot)
        
        if update.message and update.message.text == "/start":
            await handle_start(bot, update.message.chat_id)
            
    return {"statusCode": 200, "body": "ok"}
