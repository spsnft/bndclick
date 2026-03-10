import os
import json
import base64
import requests
import gspread
from google.oauth2.service_account import Credentials
from http.server import BaseHTTPRequestHandler
from datetime import datetime

# Константы из окружения
TOKEN = os.getenv("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
# Ожидаем здесь Base64 строку
GOOGLE_CREDS_B64 = os.getenv("GOOGLE_CREDENTIALS")

def log_user_to_sheet(user):
    print(f"!!! LOGGING STARTED FOR: {user.get('id')} !!!")
    try:
        if not GOOGLE_CREDS_B64:
            print("!!! ERROR: GOOGLE_CREDENTIALS variable is empty !!!")
            return

        # Декодируем Base64 в JSON
        decoded_data = base64.b64decode(GOOGLE_CREDS_B64).decode('utf-8')
        info = json.loads(decoded_data)
        
        # Исправляем переносы строк в ключе, если они превратились в текст
        if "private_key" in info:
            info["private_key"] = info["private_key"].replace("\\n", "\n")

        creds = Credentials.from_service_account_info(
            info, 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        
        user_id = str(user.get("id"))
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
            print("!!! SUCCESS: DATA WRITTEN TO SHEET !!!")
        else:
            print("!!! INFO: USER ALREADY IN SHEET !!!")
    except Exception as e:
        print(f"!!! SHEET ERROR: {str(e)} !!!")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        print("!!! POST REQUEST RECEIVED !!!")
        try:
            update = json.loads(post_data.decode('utf-8'))
            if "message" in update and update["message"].get("text") == "/start":
                chat_id = update["message"]["chat"]["id"]
                user_from = update["message"]["from"]
                
                log_user_to_sheet(user_from)
                
                url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                
                # Пост 1 (Закреп)
                p1 = {
                    "chat_id": chat_id, 
                    "text": "**🔥Всегда актуальный бот**", 
                    "reply_markup": {"inline_keyboard": [[{"text": "👤 Бот", "url": "https://t.me/bndhome_bot"}]]}, 
                    "parse_mode": "Markdown"
                }
                res = requests.post(url, json=p1).json()
                if res.get("ok"):
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/pinChatMessage", 
                                  json={"chat_id": chat_id, "message_id": res["result"]["message_id"], "disable_notification": True})
                
                # Пост 2 (Меню)
                text_main = (
                    "**БoшкyHaДoрoжкy.Phuket 🌴**\n\n"
                    "Пишите оператору - мы отвечаем максимально быстро!\n\n"
                    "Используйте кнопки ниже для быстрых переходов ⬇️\n"
                    "В случае блокировки любого ресурса - мы обновим ссылку и пришлем оповещение в этот бот😊\n\n"
                    "Спасибо, что выбираете нас и остаетесь на связи!❤️"
                )
                p2 = {
                    "chat_id": chat_id, 
                    "text": text_main, 
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "🌴 Каталог", "url": "https://bndeliveryphuket.click/info"}, {"text": "👤 Оператор", "url": "https://bndeliveryphuket.click/chat"}],
                            [{"text": "📸 Instagram", "url": "https://bndeliveryphuket.click/insta"}, {"text": "🟢 WhatsApp", "url": "https://bndeliveryphuket.click/wa"}]
                        ]
                    }, 
                    "parse_mode": "Markdown"
                }
                requests.post(url, json=p2)
        except Exception as e:
            print(f"!!! GLOBAL ERROR: {e} !!!")
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is active')
