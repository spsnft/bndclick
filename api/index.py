import os
import json
import requests
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
    # 1. СООБЩЕНИЕ ДЛЯ ЗАКРЕПА (Актуальный оператор)
    text_pin = "📍 **Всегда актуальный контакт оператора**"
    keyboard_pin = {
        "inline_keyboard": [
            [{"text": "👤 Оператор", "url": "https://bndeliveryphuket.click/chat"}]
        ]
    }
    
    res_pin = send_telegram_request("sendMessage", {
        "chat_id": chat_id,
        "text": text_pin,
        "reply_markup": keyboard_pin,
        "parse_mode": "Markdown"
    })
    
    if res_pin and res_pin.get("ok"):
        msg_id = res_pin["result"]["message_id"]
        send_telegram_request("pinChatMessage", {"chat_id": chat_id, "message_id": msg_id, "disable_notification": True})

    # 2. ОСНОВНОЕ МЕНЮ (С новыми текстами и цветами)
    text_main = (
        "**BND.Delivery Phuket 🌴**\n\n"
        "Пишите оператору - мы отвечаем максимально быстро!\n"
        "Используйте кнопки ниже для быстрых переходов и сохраняйте их себе\n"
        "В случае блокировки любого из ресурсов - мы обновим ссылку и пришлем оповещение в этот бот😊\n\n"
        "Спасибо, что выбираете нас и остаетесь на связи!❤️"
    )
    
    # Раскраска кнопок через стили
    keyboard_main = {
        "inline_keyboard": [
            [
                {"text": "🌴 Каталог", "url": "https://bndeliveryphuket.click/info"},
                {"text": "👤 Оператор", "url": "https://bndeliveryphuket.click/chat"}
            ],
            [
                {"text": "📸 Instagram", "url": "https://bndeliveryphuket.click/insta"},
                {"text": "🟢 WhatsApp", "url": "https://bndeliveryphuket.click/wa"}
            ]
        ]
    }
    
    send_telegram_request("sendMessage", {
        "chat_id": chat_id,
        "text": text_main,
        "reply_markup": keyboard_main,
        "parse_mode": "Markdown"
    })

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            update = json.loads(post_data.decode('utf-8'))
            if "message" in update and update["message"].get("text") == "/start":
                handle_start(update["message"]["chat"]["id"])
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
