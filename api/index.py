import os
import json
import requests
import gspread
from google.oauth2.service_account import Credentials
from http.server import BaseHTTPRequestHandler
from datetime import datetime

TOKEN = os.getenv("TELEGRAM_TOKEN")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

def log_user_to_sheet(user):
    print(f"DEBUG: Starting log process for user {user.get('id')}")
    try:
        if not GOOGLE_CREDENTIALS:
            print("DEBUG ERROR: GOOGLE_CREDENTIALS is missing in Environment Variables")
            return
        
        info = json.loads(GOOGLE_CREDENTIALS)
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
            print("DEBUG SUCCESS: Row added to Google Sheet")
        else:
            print("DEBUG INFO: User already in sheet")
    except Exception as e:
        print(f"DEBUG CRITICAL ERROR: {str(e)}")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            update = json.loads(post_data.decode('utf-8'))
            if "message" in update and update["message"].get("text") == "/start":
                chat_id = update["message"]["chat"]["id"]
                user_data = update["message"]["from"]
                
                # 1. Логируем (теперь внутри, чтобы видеть ошибки)
                log_user_to_sheet(user_data)
                
                # 2. Шлем сообщения в ТГ (твой актуальный вариант)
                url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                
                # Сообщение 1 (Закреп)
                payload_pin = {
                    "chat_id": chat_id,
                    "text": "**🔥Всегда актуальный бот**",
                    "reply_markup": {"inline_keyboard": [[{"text": "👤 Бот", "url": "https://t.me/bndhome_bot"}]]},
                    "parse_mode": "Markdown"
                }
                res = requests.post(url, json=payload_pin).json()
                if res.get("ok"):
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/pinChatMessage", 
                                  json={"chat_id": chat_id, "message_id": res["result"]["message_id"], "disable_notification": True})

                # Сообщение 2 (Меню)
                payload_main = {
                    "chat_id": chat_id,
                    "text": "**БoшкyHaДoрoжкy.Phuket 🌴**\n\nПишите оператору - мы отвечаем максимально быстро!\n\nИспользуйте кнопки ниже для быстрых переходов ⬇️\nВ случае блокировки любого ресурса - мы обновим ссылку и пришлем оповещение в этот бот😊\n\nСпасибо, что выбираете нас и остаетесь на сязи!❤️",
                    "reply_markup": {
                        "inline_keyboard": [
                            [{"text": "🌴 Каталог", "url": "https://bndeliveryphuket.click/info"}, {"text": "👤 Оператор", "url": "https://bndeliveryphuket.click/chat"}],
                            [{"text": "📸 Instagram", "url": "https://bndeliveryphuket.click/insta"}, {"text": "🟢 WhatsApp", "url": "https://bndeliveryphuket.click/wa"}]
                        ]
                    },
                    "parse_mode": "Markdown"
                }
                requests.post(url, json=payload_main)

        except Exception as e:
            print(f"DEBUG GLOBAL ERROR: {str(e)}")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is running...')
