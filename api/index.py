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
    # 1. ПЕРВОЕ СООБЩЕНИЕ (Для закрепа)
    text_pin = "**🔥Всегда актуальный бот**"
    keyboard_pin = {
        "inline_keyboard": [
            [{"text": "👤 Бот", "url": "https://t.me/bndhome_bot"}]
        ]
    }
    
    payload_pin = {
        "chat_id": chat_id,
        "text": text_pin,
        "reply_markup": keyboard_pin,
        "parse_mode": "Markdown"
    }
    
    res_pin = send_telegram_request("sendMessage", payload_pin)
    
    # Закрепляем это сообщение
    if res_pin and res_pin.get("ok"):
        msg_id = res_pin["result"]["message_id"]
        send_telegram_request("pinChatMessage", {
            "chat_id": chat_id, 
            "message_id": msg_id, 
            "disable_notification": True
        })

    # 2. ВТОРОЕ СООБЩЕНИЕ (Основное меню)
    text_main = (
        "**БoшкyHaДoрoжкy.Phuket 🌴**\n\n"
        "Пишите оператору - мы отвечаем максимально быстро!\n\n"
        "Используйте кнопки ниже для быстрых переходов ⬇️\n"
        "В случае блокировки любого ресурса - мы обновим ссылку и пришлем оповещение в этот бот😊\n\n"
        "Спасибо, что выбираете нас и остаетесь на сязи!❤️"
    )
    
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
    
    payload_main = {
        "chat_id": chat_id,
        "text": text_main,
        "reply_markup": keyboard_main,
        "parse_mode": "Markdown"
    }
    
    send_telegram_request("sendMessage", payload_main)

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
