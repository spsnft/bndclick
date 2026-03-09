import os
import json
import asyncio
from http.server import BaseHTTPRequestHandler
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TOKEN)

async def send_start(chat_id):
    text = "BND Delivery Phuket 🌴\n\nНапишите нам, мы ответим быстро!"
    keyboard = [
        [InlineKeyboardButton("🥥 Каталог", url="https://bndeliveryphuket.click/info"),
         InlineKeyboardButton("👤 Оператор", url="https://bndeliveryphuket.click/chat")],
        [InlineKeyboardButton("📸 Instagram", url="https://bndeliveryphuket.click/insta"),
         InlineKeyboardButton("🟢 WhatsApp", url="https://bndeliveryphuket.click/wa")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправка
    msg = await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
    # Авто-закреп
    try:
        await bot.pin_chat_message(chat_id=chat_id, message_id=msg.message_id)
    except:
        pass

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        update = json.loads(post_data.decode('utf-8'))

        if "message" in update and update["message"].get("text") == "/start":
            chat_id = update["message"]["chat"]["id"]
            asyncio.run(send_start(chat_id))

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'ok')
