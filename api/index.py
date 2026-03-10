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
    # Этот принт ДОЛЖЕН быть в логах первым
    print(f"!!! LOGGING STARTED FOR: {user.get('id')} !!!")
    try:
        raw_creds = GOOGLE_CREDENTIALS.strip().replace("\\\\n", "\\n")
        info = json.loads(raw_creds)
        if "private_key" in info:
            info["private_key"] = info["private_key"].replace("\\n", "\n")

        creds = Credentials.from_service_account_info(
            info, 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).sheet1
        
        user_id = str(user.get("id"))
        # Простая дозапись без проверки (для теста)
        row = [
            user_id,
            user.get("first_name", ""),
            user.get("last_name", ""),
            "@" + user.get("username", "") if user.get("username") else "",
            datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        ]
        sheet.append_row(row)
        print("!!! SUCCESS: DATA WRITTEN TO SHEET !!!")
    except Exception as e:
        print(f"!!! SHEET ERROR: {str(e)} !!!")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        # Сразу логируем входящий запрос
        print("!!! POST REQUEST RECEIVED !!!")
        
        try:
            update = json.loads(post_data.decode('utf-8'))
            if "message" in update and update["message"].get("text") == "/start":
                chat_id = update["message"]["chat"]["id"]
                user_from = update["message"]["from"]
                
                # Сначала пробуем записать
                log_user_to_sheet(user_from)
                
                # Потом шлем ТГ
                url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                # Закреп
                p1 = {"chat_id": chat_id, "text": "**🔥Всегда актуальный бот**", "reply_markup": {"inline_keyboard": [[{"text": "👤 Бот", "url": "https://t.me/bndhome_bot"}]]}, "parse_mode": "Markdown"}
                r = requests.post(url, json=p1).json()
                if r.get("ok"):
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/pinChatMessage", json={"chat_id": chat_id, "message_id": r["result"]["message_id"], "disable_notification": True})
                # Меню
                p2 = {"chat_id": chat_id, "text": "**БoшкyHaДoрoжкy.Phuket 🌴**\n\nПишите оператору - мы отвечаем максимально быстро!\n\nИспользуйте кнопки ниже для быстрых переходов ⬇️\nВ случае блокировки любого ресурса - мы обновим ссылку и пришлем оповещение в этот бот😊\n\nСпасибо, что выбираете нас и остаетесь на сязи!❤️", "reply_markup": {"inline_keyboard": [[{"text": "🌴 Каталог", "url": "https://bndeliveryphuket.click/info"}, {"text": "👤 Оператор", "url": "https://bndeliveryphuket.click/chat"}], [{"text": "📸 Instagram", "url": "https://bndeliveryphuket.click/insta"}, {"text": "🟢 WhatsApp", "url": "https://bndeliveryphuket.click/wa"}]]}, "parse_mode": "Markdown"}
                requests.post(url, json=p2)
        except Exception as e:
            print(f"!!! GLOBAL ERROR: {e} !!!")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is active and watching')
