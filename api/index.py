import os
import json
import requests  # Мы переходим на обычные запросы для надежности на Vercel
from http.server import BaseHTTPRequestHandler

TOKEN = os.getenv("TELEGRAM_TOKEN")

def send_telegram_request(method, payload):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.json()
    except Exception as e:
        print(f"Request error: {e}")
        return None

def handle_start(chat_id):
    # 1. Отправляем основной пост с кнопками
    text = (
        "BND Delivery Phuket 🌴\n\n"
        "Напишите нам в чат, мы ответим максимально быстро!\n"
        "Используйте кнопки ниже для заказа:"
    )
    
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "🥥 Каталог", "url": "https://bndeliveryphuket.click/info"},
                {"text": "👤 Оператор", "url": "https://bndeliveryphuket.click/chat"}
            ],
            [
                {"text": "📸 Instagram", "url": "https://bndeliveryphuket.click/insta"},
                {"text": "🟢 WhatsApp", "url": "https://bndeliveryphuket.click/wa"}
            ]
        ]
    }
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": keyboard,
        "parse_mode": "Markdown"
    }
    
    result = send_telegram_request("sendMessage", payload)
    
    # 2. АВТО-ЗАКРЕП (если сообщение отправилось успешно)
    if result and result.get("ok"):
        message_id = result["result"]["message_id"]
        pin_payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "disable_notification": True
        }
        send_telegram_request("pinChatMessage", pin_payload)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            update = json.loads(post_data.decode('utf-8'))
            if "message" in update:
                msg = update["message"]
                if msg.get("text") == "/start":
                    handle_start(msg["chat"]["id"])
        except Exception as e:
            print(f"Update error: {e}")

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'ok')

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running...')
