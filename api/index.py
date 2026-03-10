import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials
from http.server import BaseHTTPRequestHandler
from datetime import datetime

# Подтягиваем переменные из настроек Vercel
TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

def log_user(user):
    try:
        if not GOOGLE_CREDENTIALS:
            print("ERROR: GOOGLE_CREDENTIALS variable is empty")
            return
        if not SPREADSHEET_ID:
            print("ERROR: SPREADSHEET_ID variable is empty")
            return
        
        # Авторизация в Google
        info = json.loads(GOOGLE_CREDENTIALS)
        creds = Credentials.from_service_account_info(
            info, 
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        client = gspread.authorize(creds)
        
        # Открываем таблицу
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        
        user_id = str(user.get("id"))
        
        # Получаем все ID из первой колонки для проверки на дубликаты
        existing_ids = sheet.col_values(1)
        
        if user_id not in existing_ids:
            row = [
                user_id,
                user.get("first_name", ""),
                user.get("last_name", ""),
                "@" + user.get("username", "") if user.get("username") else "",
                datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            ]
            sheet.append_row(row)
            print(f"SUCCESS: User {user_id} added to sheet")
        else:
            print(f"INFO: User {user_id} already exists in sheet")
            
    except Exception as e:
        print(f"Google Sheets Error: {e}")

def send_telegram_request(method, payload):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    try:
        res = requests.post(url, json=payload, timeout=10)
        return res.json()
    except Exception as e:
        print(f"Telegram Request Error: {e}")
        return None

def handle_start(chat_id, user):
    # Пытаемся записать данные в таблицу
    log_user(user)

    # 1. ПЕРВОЕ СООБЩЕНИЕ (Для закрепа)
    text_pin = "**🔥Всегда актуальный бот**"
    keyboard_pin = {
        "inline_keyboard": [
            [{"text": "👤 Бот", "url": "https://t.me/bndhome_bot"}]
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
            if "message" in update:
                msg = update["message"]
                if msg.get("text") == "/start":
                    handle_start(msg["chat"]["id"], msg["from"])
        except Exception as e:
            print(f"Update processing error: {e}")

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'ok')

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Bot is running...')
