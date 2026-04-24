import os
import json
import base64
import requests
import gspread
import time # Нужно для пауз
from google.oauth2.service_account import Credentials
from http.server import BaseHTTPRequestHandler
from datetime import datetime

# --- CONFIG ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

# ВСТАВЬ СЮДА СВОЙ ID (цифрами)
ADMIN_ID = 8699481380  
TEST_USERS = [8699481380, 91937473] # Список для тестовой рассылки

# Ссылки
URL_CATALOG = "https://bnd.delivery"
URL_OPERATOR = "https://t.me/bshk_phuket"
URL_INSTA = "https://www.instagram.com/boshkunadoroshku"
URL_WA = "https://bndeliveryphuket.click/wa"
URL_SELF = "https://bndeliveryphuket.click"

def get_sheet():
    decoded_data = base64.b64decode(GOOGLE_CREDENTIALS).decode('utf-8')
    info = json.loads(decoded_data)
    if "private_key" in info:
        info["private_key"] = info["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).sheet1

def log_user_to_sheet(user):
    try:
        sheet = get_sheet()
        user_id = str(user.get("id"))
        existing_ids = sheet.col_values(1)
        if user_id not in existing_ids:
            row = [user_id, user.get("first_name", ""), user.get("last_name", ""), "@" + user.get("username", "") if user.get("username") else "", datetime.now().strftime("%d.%m.%Y %H:%M:%S")]
            sheet.append_row(row)
    except Exception as e: print(f"!!! SHEET ERROR: {e} !!!")

def send_msg(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    if keyboard: payload["reply_markup"] = {"inline_keyboard": keyboard}
    return requests.post(url, json=payload).json()

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # СРАЗУ отвечаем OK, чтобы Telegram не присылал повторы
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'ok')

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        try:
            update = json.loads(post_data.decode('utf-8'))
            if "message" in update:
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "")
                user_id = msg["from"]["id"]

                # 1. ТЕСТОВАЯ РАССЫЛКА (На твои 2 ID)
                if text.startswith("/broadcast "):
                    if user_id == ADMIN_ID:
                        broadcast_text = text.replace("/broadcast ", "")
                        count = 0
                        for uid in TEST_USERS:
                            try:
                                send_msg(uid, broadcast_text)
                                count += 1
                                time.sleep(0.3)
                            except: continue
                        send_msg(ADMIN_ID, f"✅ Рассылка завершена. Отправлено: {count}")
                    else:
                        send_msg(chat_id, "❌ Доступ запрещен.")

                # 2. РЕАЛЬНАЯ РАССЫЛКА ПО ВСЕЙ ТАБЛИЦЕ
                elif text.startswith("/finalbroadcast "):
                    if user_id == ADMIN_ID:
                        final_text = text.replace("/finalbroadcast ", "")
                        sheet = get_sheet()
                        all_ids = sheet.col_values(1)[1:] # Пропускаем заголовок
                        
                        count = 0
                        for uid in all_ids:
                            try:
                                send_msg(uid, final_text)
                                count += 1
                                time.sleep(0.3) 
                            except: continue
                        send_msg(ADMIN_ID, f"✅ Рассылка завершена. Отправлено: {count}")
                    else:
                        send_msg(chat_id, "❌ Доступ запрещен.")

                # 3. ОБЫЧНЫЙ /START
                elif text == "/start":
                    log_user_to_sheet(msg["from"])
                    send_msg(chat_id, "**🔥Всегда актуальный бот**", [[{"text": "👤 Актуальный бот", "url": URL_SELF}]])
                    
                    main_text = (
                        "*БoшкyHaДoрoжкy | BND.delivery 🌴*\n"
                        "Напишите оператору — мы ответим максимально быстро!\n\n"
                        "_В случае блокировки любого ресурса — мы обновим ссылку и пришлем оповещение в этот бот 😊_\n\n"
                        "_А если заблокируют самого бота — жмите на кнопку '👤 Актуальный бот' в закрепе, она будет актуальна всегда_\n\n"
                        "Используйте кнопки ниже ⬇️⬇️⬇️"
                    )
                    kb = [[{"text": "🌴 Каталог", "url": URL_CATALOG}, {"text": "👤 Оператор", "url": URL_OPERATOR}],
                          [{"text": "📸 Instagram", "url": URL_INSTA}, {"text": "🟢 WhatsApp", "url": URL_WA}]]
                    send_msg(chat_id, main_text, kb)

        except Exception as e: print(f"!!! ERROR: {e} !!!")

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'active')
