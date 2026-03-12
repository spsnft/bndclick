import os
import json
import base64
import requests
import gspread
from google.oauth2.service_account import Credentials
from http.server import BaseHTTPRequestHandler
from datetime import datetime

# --- CONFIG ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

# Ссылки (изменяй их тут при необходимости)
URL_CATALOG = "https://bndeliveryphuket.click/info"
URL_OPERATOR = "https://bndeliveryphuket.click/chat"
URL_INSTA = "https://bndeliveryphuket.click/insta"
URL_WA = "https://bndeliveryphuket.click/wa"
URL_SELF = "https://bndeliveryphuket.click"

def log_user_to_sheet(user):
    try:
        if not GOOGLE_CREDENTIALS:
            return
        decoded_data = base64.b64decode(GOOGLE_CREDENTIALS).decode('utf-8')
        info = json.loads(decoded_data)
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
    except Exception as e:
        print(f"!!! SHEET ERROR: {str(e)} !!!")

def send_msg(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": text, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": True # Чтобы ссылки не плодили лишние превью
    }
    if keyboard:
        payload["reply_markup"] = {"inline_keyboard": keyboard}
    return requests.post(url, json=payload).json()

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            update = json.loads(post_data.decode('utf-8'))
            if "message" in update:
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "")
                user_from = msg["from"]

                if text == "/start":
                    # 1. Логируем в таблицу
                    log_user_to_sheet(user_from)
                    
                    # 2. Пост 1 (Закреп)
                    res = send_msg(chat_id, "**🔥Всегда актуальный бот**", [[{"text": "👤 Актуальный бот", "url": URL_SELF}]])
                    if res.get("ok"):
                        requests.post(
                            f"https://api.telegram.org/bot{TOKEN}/pinChatMessage", 
                            json={"chat_id": chat_id, "message_id": res["result"]["message_id"], "disable_notification": True}
                        )
                    
                    # 3. Пост 2 (Меню с цитатами)
                    main_text = (
                        "**БoшкyHaДoрoжкy.Phuket 🌴**\n"
                        "Напишите оператору — мы ответим максимально быстро!\n\n"
                        "> В случае блокировки любого ресурса — мы обновим ссылку и пришлем оповещение в этот бот 😊\n\n"
                        "> А если заблокируют этого бота — жмите на кнопку '👤 Актуальный бот' в закреплённом сообщении — она всегда будет работать 👌\n\n"
                        "Используйте кнопки ниже для быстрых переходов ⬇️⬇️⬇️\n\n"
                        "Спасибо, что выбираете нас и остаетесь на связи! ❤️"
                    )
                    kb = [
                        [{"text": "🌴 Каталог", "url": URL_CATALOG}, {"text": "👤 Оператор", "url": URL_OPERATOR}],
                        [{"text": "📸 Instagram", "url": URL_INSTA}, {"text": "🟢 WhatsApp", "url": URL_WA}]
                    ]
                    send_msg(chat_id, main_text, kb)
                
                elif text == "/chat":
                    send_msg(chat_id, "Нажми кнопку ниже, чтобы перейти в чат с оператором:", [[{"text": "👤 Оператор", "url": URL_OPERATOR}]])
                
                elif text == "/catalog":
                    send_msg(chat_id, "Нажми кнопку ниже, чтобы открыть наш актуальный каталог:", [[{"text": "🌴 Каталог", "url": URL_CATALOG}]])

        except Exception as e:
            print(f"!!! GLOBAL ERROR: {e} !!!")
        
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Bot is active')
