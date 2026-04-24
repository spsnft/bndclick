import os
import json
import base64
import requests
import gspread
import time 
from google.oauth2.service_account import Credentials
from http.server import BaseHTTPRequestHandler
from datetime import datetime

# --- CONFIG ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

ADMIN_ID = 8699481380  
TEST_USERS = [8699481380, 91937473] 

URL_CATALOG = "https://bnd.delivery"
URL_OPERATOR = "https://t.me/bshk_phuket"
URL_INSTA = "https://www.instagram.com/boshkunadoroshku"
URL_WA = "https://bndeliveryphuket.click/wa"
URL_SELF = "https://bndeliveryphuket.click"

def get_ss():
    decoded_data = base64.b64decode(GOOGLE_CREDENTIALS).decode('utf-8')
    info = json.loads(decoded_data)
    if "private_key" in info:
        info["private_key"] = info["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
    return gspread.authorize(creds).open_by_key(SPREADSHEET_ID)

def update_user_status(user_id, status):
    try:
        ss = get_ss()
        sheet = ss.sheet1
        cells = sheet.findall(str(user_id))
        if cells:
            row_idx = cells[0].row
            sheet.update_cell(row_idx, 6, status) # 6-я колонка — статус
            sheet.update_cell(row_idx, 5, datetime.now().strftime("%d.%m.%Y %H:%M:%S")) # Обновляем дату активности
    except Exception as e: print(f"!!! STATUS UPDATE ERROR: {e} !!!")

def log_broadcast(b_type, text, success, errors, duration):
    try:
        ss = get_ss()
        sheet = ss.worksheet("Broadcasts")
        row = [datetime.now().strftime("%d.%m.%Y %H:%M:%S"), b_type, text[:100], success, errors, round(duration, 2)]
        sheet.append_row(row)
    except Exception as e: print(f"!!! LOG ERROR: {e} !!!")

def log_user_to_sheet(user):
    try:
        sheet = get_ss().sheet1
        user_id = str(user.get("id"))
        cells = sheet.findall(user_id)
        
        now_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        if not cells:
            row = [user_id, user.get("first_name", ""), user.get("last_name", ""), "@" + user.get("username", "") if user.get("username") else "", now_str, "Active"]
            sheet.append_row(row)
        else:
            update_user_status(user_id, "Active")
    except Exception as e: print(f"!!! SHEET ERROR: {e} !!!")

def send_msg(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    if keyboard: payload["reply_markup"] = {"inline_keyboard": keyboard}
    res = requests.post(url, json=payload).json()
    return res

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
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

                if text.startswith("/broadcast "):
                    if user_id == ADMIN_ID:
                        start_time = time.time()
                        broadcast_text = text.replace("/broadcast ", "")
                        count, errs = 0, 0
                        for uid in TEST_USERS:
                            res = send_msg(uid, broadcast_text)
                            if res.get("ok"): count += 1
                            else: errs += 1
                            time.sleep(0.3)
                        log_broadcast("TEST", broadcast_text, count, errs, time.time() - start_time)
                        send_msg(ADMIN_ID, f"✅ Тест завершен. Отправлено: {count}")

                elif text.startswith("/finalbroadcast "):
                    if user_id == ADMIN_ID:
                        start_time = time.time()
                        final_text = text.replace("/finalbroadcast ", "")
                        sheet = get_ss().sheet1
                        all_ids = sheet.col_values(1)[1:] 
                        
                        count, errs = 0, 0
                        for uid in all_ids:
                            try:
                                res = send_msg(uid, final_text)
                                if res.get("ok"):
                                    count += 1
                                else:
                                    errs += 1
                                    # Если бот заблокирован — помечаем в таблице
                                    if "blocked" in res.get("description", "").lower():
                                        update_user_status(uid, "Blocked")
                                time.sleep(0.3) 
                            except: 
                                errs += 1
                                continue
                        
                        log_broadcast("FINAL", final_text, count, errs, time.time() - start_time)
                        send_msg(ADMIN_ID, f"✅ Рассылка завершена. Отправлено: {count}")

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
