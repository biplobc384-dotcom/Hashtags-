import telebot
from telebot import types
import json
import os
import random
import requests
import urllib.parse
import base64
import threading
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image
from flask import Flask
from dotenv import load_dotenv

# ================= কনফিগারেশন =================
load_dotenv()

# টোকেন সেটআপ
API_TOKEN = os.getenv('BOT_TOKEN') 
if not API_TOKEN:
    API_TOKEN = 'YOUR_BOT_TOKEN_HERE' 

ADMIN_ID = 6740599881 
BOT_USERNAME = "@HashtagMasterPro_Bot" 
FORCE_SUB_CHANNEL = "@ArifurHackworld" 
GAME_URL = "https://biplobc384-dotcom.github.io/gamezone" 

# API Keys
RMBG_API_KEY = "QijuTptTcicEgtSVwE3KKx4d"
OCR_API_KEY = "helloworld" 

# খরচ সেটিংস
COST_PER_POST = 20
COST_PER_IMAGE = 30
COST_PER_QR = 10
COST_PER_TTS = 10
COST_PER_BG = 20
COST_PER_SS = 15
COST_PER_PDF = 10
COST_PER_OCR = 10
COST_PER_AI_CHAT = 20
COST_PER_WEATHER = 10
COST_PER_CRYPTO = 10
COST_PER_FAKE_ID = 10
COST_PER_SITE = 10
COST_PER_BIN = 10
COST_PER_LYRICS = 10
COST_PER_SHORTEN = 5
COST_PER_PRAYER = 5
COST_PER_REPEAT = 5
COST_PER_MEME = 10

# ফাইল পাথ
DATA_FILE = "users.json"
CODES_FILE = "codes.json"

bot = telebot.TeleBot(API_TOKEN)
user_temp_data = {} 
chat_queue = []
file_lock = threading.Lock() 

# ================= Render Web Server =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Cyber Bot 20.0 (All Features) is Running! 🔥"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ================= ডাটাবেস ও হেল্পার =================
def load_json(filename):
    if not os.path.exists(filename): return {}
    with open(filename, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

def save_json(filename, data):
    with file_lock:
        with open(filename, 'w', encoding='utf-8') as f: 
            json.dump(data, f, indent=4, ensure_ascii=False)

def load_codes(): return load_json(CODES_FILE)
def save_codes(data): save_json(CODES_FILE, data)

def get_user_data(user_id):
    data = load_json(DATA_FILE)
    uid = str(user_id)
    if uid not in data: 
        data[uid] = {
            'name': 'Unknown', 'points': 50, 'bank': 0, 
            'joined': str(datetime.now()), 'streak': 0, 
            'last_bonus': '', 'last_interest': ''
        }
        save_json(DATA_FILE, data)
    
    if 'bank' not in data[uid]: data[uid]['bank'] = 0
    if 'streak' not in data[uid]: data[uid]['streak'] = 0
    save_json(DATA_FILE, data)
    return data[uid]

def update_points(user_id, amount):
    data = load_json(DATA_FILE)
    uid = str(user_id)
    if uid not in data: get_user_data(user_id)
    data[uid]['points'] = data[uid].get('points', 0) + amount
    save_json(DATA_FILE, data)
    return data[uid]['points']

def get_points(user_id):
    data = load_json(DATA_FILE)
    return data.get(str(user_id), {}).get('points', 0)
# ================= সাবস্ক্রিপশন চেক =================
def is_subscribed(user_id):
    if not FORCE_SUB_CHANNEL: return True
    try:
        status = bot.get_chat_member(FORCE_SUB_CHANNEL, user_id).status
        return status in ['creator', 'administrator', 'member']
    except:
        return True 

def get_sub_keyboard():
    mk = types.InlineKeyboardMarkup()
    mk.add(types.InlineKeyboardButton("📢 চ্যানেলে জয়েন করুন", url=f"https://t.me/{FORCE_SUB_CHANNEL.replace('@','')}"))
    mk.add(types.InlineKeyboardButton("✅ জয়েন করেছি", callback_data="check_sub"))
    return mk

# ================= সম্পূর্ণ মেনু সিস্টেম =================
def get_home_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🤖 এআই ও ক্রিয়েশন", "🛠 ইউটিলিটি টুলস")
    markup.add("💻 সাইবার ও টেক", "🎮 ফান ও গেমস") 
    markup.add("🏦 ব্যাংক ও লটারি", "👤 প্রোফাইল ও ব্যালেন্স") 
    if user_id == ADMIN_ID: markup.add("👑 অ্যাডমিন প্যানেল")
    return markup

def get_ai_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🤖 এআই চ্যাট", "🎨 এআই ছবি")
    markup.add("📝 পোস্ট মেকার", "🗣️ টেক্সট টু স্পিচ")
    markup.add("✍️ বানান চেক", "🖼️ OCR (ছবি->টেক্সট)")
    markup.add("🔙 মেইন মেনু")
    return markup

def get_utility_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🖼️ ব্যাকগ্রাউন্ড রিমুভ", "🌤 লাইভ আবহাওয়া") 
    markup.add("📱 QR মেকার", "📄 ছবি থেকে PDF")
    markup.add("📸 4K স্ক্রিনশট", "🔗 ইউআরএল শর্টনার")
    markup.add("🔁 টেক্সট রিপিটার", "🌐 অনুবাদক")
    markup.add("🕋 নামাজের সময়সূচি", "🔙 মেইন মেনু")
    return markup

def get_cyber_menu(): 
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🔐 Base64 টুল", "💳 BIN চেকার")
    markup.add("💰 ক্রিপ্টো রেট", "✅ সাইট স্ট্যাটাস")
    markup.add("👤 ফেইক আইডি", "🗣️ অ্যানোনিমাস চ্যাট") 
    markup.add("🔙 মেইন মেনু")
    return markup

def get_fun_menu(user_id):
    user_points = get_points(user_id)
    game_url_with_params = f"{GAME_URL}?points={user_points}"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton(text="🎮 প্লে সাইবার আর্কেড (Start)", web_app=types.WebAppInfo(url=game_url_with_params)))
    markup.add("🎼 লিরিক্স ফাইন্ডার", "🐸 বাংলা মিম") 
    markup.add("🔙 মেইন মেনু")
    return markup

def get_bank_menu(): 
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📥 টাকা জমা (Deposit)", "📤 টাকা উত্তোলন (Withdraw)")
    markup.add("📈 সুদ সংগ্রহ (Interest)", "🎰 লটারি কিনুন (100 Pt)")
    markup.add("🔙 মেইন মেনু")
    return markup

def get_admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("💾 ব্যাকআপ", "📂 রিস্টোর") 
    markup.add("📢 ব্রডকাস্ট", "➕ পয়েন্ট অ্যাড")
    markup.add("🎲 লটারি ড্র", "🔙 মেইন মেনু") 
    return markup

def get_cancel_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("❌ বাতিল করুন")
    return markup

# ================= API Functions =================
def get_ai_image(prompt):
    try: return requests.get(f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}").content
    except: return None

def remove_bg(image_file):
    try:
        return requests.post("https://api.remove.bg/v1.0/removebg", files={'image_file': image_file}, data={'size': 'auto'}, headers={'X-Api-Key': RMBG_API_KEY}).content
    except: return None

def get_ocr_text(image_bytes):
    try:
        url = "https://api.ocr.space/parse/image"
        files = {'file': ('image.jpg', image_bytes, 'image/jpeg')}
        payload = {'apikey': OCR_API_KEY, 'language': 'eng'}
        r = requests.post(url, files=files, data=payload, timeout=15)
        return r.json()['ParsedResults'][0]['ParsedText']
    except: return None
# ================= মেইন হ্যান্ডলার =================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.from_user.id
    if not is_subscribed(uid):
        bot.send_message(message.chat.id, "⚠️ বটটি ব্যবহার করতে আমাদের চ্যানেলে জয়েন করুন!", reply_markup=get_sub_keyboard())
        return
    get_user_data(uid)
    bot.reply_to(message, "👋 **আসসালামু আলাইকুম!**\nCyber Bot 20.0 (All Features Restored)", parse_mode="Markdown", reply_markup=get_home_menu(uid))

@bot.message_handler(content_types=['web_app_data'])
def web_app_data_handler(message):
    uid = str(message.from_user.id)
    try:
        data = json.loads(message.web_app_data.data)
        new_balance = int(data.get('points', 0)) 
        db_data = load_json(DATA_FILE)
        if uid not in db_data: get_user_data(uid)
        db_data[uid]['points'] = new_balance
        save_json(DATA_FILE, db_data)
        bot.send_message(message.chat.id, f"🎮 **গেম আপডেট:**\n💰 ব্যালেন্স: {new_balance}")
    except Exception as e: bot.send_message(message.chat.id, f"⚠️ Error: {e}")

# --- File Handler (Backup, BG, OCR, PDF) ---
@bot.message_handler(content_types=['document', 'photo'])
def handle_files(message):
    cid = message.chat.id
    uid = message.from_user.id

    if uid == ADMIN_ID and cid in user_temp_data and user_temp_data[cid].get('action') == 'restore_db':
        try:
            if message.content_type == 'document' and message.document.file_name == "users.json":
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                with open(DATA_FILE, 'wb') as new_file: new_file.write(downloaded_file)
                bot.reply_to(message, "✅ **রিস্টোর সফল!**", reply_markup=get_admin_menu())
                user_temp_data.pop(cid)
            else: bot.reply_to(message, "❌ ভুল ফাইল।")
        except: bot.reply_to(message, "❌ এরর।")

    elif cid in user_temp_data:
        action = user_temp_data[cid].get('action')
        
        if message.content_type == 'photo':
            file_info = bot.get_file(message.photo[-1].file_id)
            img_data = bot.download_file(file_info.file_path)

            if action == 'remove_bg':
                bot.reply_to(message, "⚙️ প্রসেসিং...")
                res = remove_bg(img_data)
                if res:
                    bot.send_document(cid, BytesIO(res), caption="✅ নো ব্যাকগ্রাউন্ড", visible_file_name="no_bg.png")
                    update_points(uid, -COST_PER_BG)
                else: bot.reply_to(message, "❌ ফেইলড।")
                
            elif action == 'ocr_scan':
                bot.reply_to(message, "⚙️ স্ক্যান হচ্ছে...")
                txt = get_ocr_text(img_data)
                if txt:
                    bot.reply_to(message, f"📝 **টেক্সট:**\n{txt}")
                    update_points(uid, -COST_PER_OCR)
                else: bot.reply_to(message, "❌ টেক্সট পাওয়া যায়নি।")

            elif action == 'img_to_pdf':
                try:
                    pdf_bytes = BytesIO()
                    image = Image.open(BytesIO(img_data)).convert('RGB')
                    image.save(pdf_bytes, format='PDF')
                    pdf_bytes.seek(0)
                    bot.send_document(cid, pdf_bytes, caption="📄 PDF তৈরি!", visible_file_name="image.pdf")
                    update_points(uid, -COST_PER_PDF)
                except: bot.reply_to(message, "❌ এরর।")

        if cid in user_temp_data: user_temp_data.pop(cid)

# ================= ALL FEATURES LOGIC =================
@bot.message_handler(func=lambda m: True)
def handle_text(message):
    cid = message.chat.id
    uid = message.from_user.id
    text = message.text

    # --- ADMIN ---
    if uid == ADMIN_ID:
        if text == "💾 ব্যাকআপ":
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "rb") as file:
                    bot.send_document(cid, file, caption=f"💾 Backup: {datetime.now()}", visible_file_name="users.json")
            else: bot.reply_to(message, "⚠️ ফাইল নেই।")
            return
        elif text == "📂 রিস্টোর":
            user_temp_data[cid] = {'action': 'restore_db'}
            bot.reply_to(message, "📂 `users.json` ফাইল দিন:", reply_markup=get_cancel_menu())
            return
        elif text == "📢 ব্রডকাস্ট":
            user_temp_data[cid] = {'action': 'broadcast'}
            bot.reply_to(message, "📢 মেসেজ লিখুন:", reply_markup=get_cancel_menu())
            return
        elif text == "➕ পয়েন্ট অ্যাড":
            user_temp_data[cid] = {'action': 'admin_add_point_id'}
            bot.reply_to(message, "👤 User ID দিন:", reply_markup=get_cancel_menu())
            return

    # --- INPUT PROCESSING ---
    if cid in user_temp_data:
        action = user_temp_data[cid].get('action')

        if action == 'broadcast' and uid == ADMIN_ID:
            data = load_json(DATA_FILE)
            for u in data:
                try: bot.send_message(u, f"📢 **নোটিশ:**\n\n{text}", parse_mode="Markdown")
                except: pass
            bot.reply_to(message, "✅ ব্রডকাস্ট সম্পন্ন।", reply_markup=get_admin_menu())
            user_temp_data.pop(cid)
            return

        elif action == 'admin_add_point_id':
            user_temp_data[cid] = {'action': 'admin_add_point_amount', 'target': text}
            bot.reply_to(message, "💰 কত পয়েন্ট?", reply_markup=get_cancel_menu())
            return

        elif action == 'admin_add_point_amount':
            try:
                update_points(user_temp_data[cid]['target'], int(text))
                bot.reply_to(message, "✅ Done.", reply_markup=get_admin_menu())
            except: bot.reply_to(message, "❌ Error.", reply_markup=get_admin_menu())
            user_temp_data.pop(cid)
            return

        # --- AI & TOOLS ---
        elif action == 'ai_image':
            bot.send_chat_action(cid, 'upload_photo')
            img = get_ai_image(text)
            if img:
                bot.send_photo(cid, img, caption="🎨 Generated by AI")
                update_points(uid, -COST_PER_IMAGE)
            else: bot.reply_to(message, "❌ ফেইলড।")
            user_temp_data.pop(cid)
            return
        
        elif action == 'post_maker':
            bot.send_chat_action(cid, 'typing')
            try:
                res = requests.get(f"https://text.pollinations.ai/{urllib.parse.quote('Write a social media post about: '+text)}").text
                bot.reply_to(message, f"📝 **পোস্ট:**\n{res}")
                update_points(uid, -COST_PER_POST)
            except: bot.reply_to(message, "❌ এরর।")
            user_temp_data.pop(cid)
            return

        elif action == 'ai_chat':
            bot.send_chat_action(cid, 'typing')
            try:
                res = requests.get(f"https://text.pollinations.ai/{urllib.parse.quote('Reply in Bengali: '+text)}").text
                bot.reply_to(message, res, reply_markup=get_home_menu(uid))
                update_points(uid, -COST_PER_AI_CHAT)
            except: bot.reply_to(message, "⚠️ বিজি।")
            user_temp_data.pop(cid)
            return

        elif action == 'text_to_speech':
            try:
                from gtts import gTTS
                tts = gTTS(text, lang='bn')
                f = BytesIO(); tts.write_to_fp(f); f.seek(0)
                bot.send_audio(cid, f, caption="🔊 Audio")
                update_points(uid, -COST_PER_TTS)
            except: bot.reply_to(message, "❌ সমস্যা।")
            user_temp_data.pop(cid)
            return
            
        elif action == 'spell_check':
            try:
                res = requests.get(f"https://text.pollinations.ai/{urllib.parse.quote('Correct spelling: '+text)}").text
                bot.reply_to(message, f"✅ কারেকশন:\n{res}")
            except: bot.reply_to(message, "❌ এরর।")
            user_temp_data.pop(cid)
            return

        # --- UTILITY ---
        elif action == 'weather_check':
            try:
                url = f"http://api.weatherapi.com/v1/current.json?key=e868212133404c01b44123547231406&q={text}"
                w = requests.get(url).json()
                msg = f"🌤 **আবহাওয়া ({w['location']['name']})**\nতাপমাত্রা: {w['current']['temp_c']}°C\nঅবস্থা: {w['current']['condition']['text']}"
                bot.reply_to(message, msg)
                update_points(uid, -COST_PER_WEATHER)
            except: bot.reply_to(message, "❌ নাম ভুল।")
            user_temp_data.pop(cid)
            return

        elif action == 'qr_make':
            try:
                url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={text}"
                bot.send_photo(cid, url, caption="📱 QR Code")
                update_points(uid, -COST_PER_QR)
            except: bot.reply_to(message, "❌ এরর।")
            user_temp_data.pop(cid)
            return

        elif action == 'ss_web':
            try:
                url = f"https://image.thum.io/get/width/1920/crop/1080/noanimate/{text}"
                bot.send_photo(cid, url, caption="📸 স্ক্রিনশট")
                update_points(uid, -COST_PER_SS)
            except: bot.reply_to(message, "❌ লিংক ভুল।")
            user_temp_data.pop(cid)
            return
            
        elif action == 'translator':
            try:
                res = requests.get(f"https://text.pollinations.ai/{urllib.parse.quote('Translate to Bengali: '+text)}").text
                bot.reply_to(message, f"🌐 **অনুবাদ:**\n{res}")
            except: bot.reply_to(message, "❌ এরর।")
            user_temp_data.pop(cid)
            return

        elif action == 'repeater_text':
            user_temp_data[cid]['text_to_repeat'] = text
            user_temp_data[cid]['action'] = 'repeater_count'
            bot.reply_to(message, "🔢 কতবার?", reply_markup=get_cancel_menu())
            return
            
        elif action == 'repeater_count':
            try:
                count = int(text)
                if count > 2000: count = 2000
                res = (user_temp_data[cid]['text_to_repeat'] + " ") * count
                if len(res) > 4000:
                    f = BytesIO(res.encode()); f.name = "repeat.txt"
                    bot.send_document(cid, f, caption="✅ ফাইল।")
                else: bot.reply_to(message, res)
                update_points(uid, -COST_PER_REPEAT)
            except: bot.reply_to(message, "❌ সংখ্যা দিন।")
            user_temp_data.pop(cid)
            return

        # --- CYBER & FUN ---
        elif action == 'base64_tool':
            try:
                encoded = base64.b64encode(text.encode()).decode()
                bot.reply_to(message, f"🔐 **Encoded:** `{encoded}`", parse_mode="Markdown")
            except: bot.reply_to(message, "❌ এরর।")
            user_temp_data.pop(cid)
            return

        elif action == 'bin_check':
            try:
                r = requests.get(f"https://lookup.binlist.net/{text[:6]}").json()
                msg = f"💳 **BIN Info**\nBank: {r.get('bank',{}).get('name')}\nCountry: {r.get('country',{}).get('name')}"
                bot.reply_to(message, msg)
                update_points(uid, -COST_PER_BIN)
            except: bot.reply_to(message, "❌ ভুল BIN।")
            user_temp_data.pop(cid)
            return

        elif action == 'crypto_rate':
            try:
                r = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={text.upper()}USDT").json()
                bot.reply_to(message, f"💰 {text.upper()}: ${r['price']}")
                update_points(uid, -COST_PER_CRYPTO)
            except: bot.reply_to(message, "❌ ভুল কয়েন (e.g. BTC)।")
            user_temp_data.pop(cid)
            return

        elif action == 'site_check':
            try:
                r = requests.get(text)
                status = "✅ অনলাইন" if r.status_code == 200 else f"❌ অফলাইন ({r.status_code})"
                bot.reply_to(message, f"🌐 সাইট: {text}\nঅবস্থা: {status}")
                update_points(uid, -COST_PER_SITE)
            except: bot.reply_to(message, "❌ এরর।")
            user_temp_data.pop(cid)
            return

        elif action == 'lyrics_find':
            try:
                r = requests.get(f"https://lyrist.vercel.app/api/{text}").json()
                lyrics = r.get('lyrics', 'পাওয়া যায়নি')
                if len(lyrics) > 4000: lyrics = lyrics[:4000]
                bot.reply_to(message, f"🎼 **লিরিক্স:**\n\n{lyrics}")
                update_points(uid, -COST_PER_LYRICS)
            except: bot.reply_to(message, "❌ পাওয়া যায়নি।")
            user_temp_data.pop(cid)
            return

        elif action == 'url_shorten':
            try:
                res = requests.get(f"http://tinyurl.com/api-create.php?url={text}").text
                bot.reply_to(message, f"🔗 লিংক: {res}")
                update_points(uid, -COST_PER_SHORTEN)
            except: bot.reply_to(message, "❌ এরর।")
            user_temp_data.pop(cid)
            return

        elif action == 'prayer_time':
            try:
                date_str = datetime.now().strftime("%d-%m-%Y")
                url = f"http://api.aladhan.com/v1/timingsByCity?city={text}&country=Bangladesh&method=1"
                req = requests.get(url).json()
                
                if req['code'] == 200:
                    t = req['data']['timings']
                    msg = (f"🕋 **নামাজের সময়সূচি ({text})**\n"
                           f"📅 তারিখ: {req['data']['date']['readable']}\n\n"
                           f"ফজর: {t['Fajr']}\n"
                           f"জোহর: {t['Dhuhr']}\n"
                           f"আছর: {t['Asr']}\n"
                           f"মাগরিব: {t['Maghrib']}\n"
                           f"এশা: {t['Isha']}")
                    bot.reply_to(message, msg)
                    update_points(uid, -COST_PER_PRAYER)
                else:
                    bot.reply_to(message, "❌ শহরের নাম সঠিক দিন (ইংরেজিতে)।")
            except Exception as e:
                bot.reply_to(message, "❌ তথ্য পাওয়া যায়নি।")
            
            if cid in user_temp_data:
                user_temp_data.pop(cid)
            return

    # --- মেনু ন্যাভিগেশন ---
    if text == "🤖 এআই ও ক্রিয়েশন":
        bot.send_message(cid, "🤖 AI মেনু:", reply_markup=get_ai_menu())
    elif text == "🛠 ইউটিলিটি টুলস":
        bot.send_message(cid, "🛠 টুলস মেনু:", reply_markup=get_utility_menu())
    elif text == "💻 সাইবার ও টেক":
        bot.send_message(cid, "💻 সাইবার মেনু:", reply_markup=get_cyber_menu())
    elif text == "🎮 ফান ও গেমস":
        bot.send_message(cid, "🎮 ফান মেনু:", reply_markup=get_fun_menu(uid))
    elif text == "🏦 ব্যাংক ও লটারি":
        bot.send_message(cid, "🏦 ব্যাংক মেনু:", reply_markup=get_bank_menu())
    elif text == "👑 অ্যাডমিন প্যানেল" and uid == ADMIN_ID:
        bot.send_message(cid, "👑 অ্যাডমিন প্যানেল:", reply_markup=get_admin_menu())
    elif text == "🔙 মেইন মেনু":
        bot.send_message(cid, "🏠 মেইন মেনু:", reply_markup=get_home_menu(uid))
    elif text == "👤 প্রোফাইল ও ব্যালেন্স":
        data = get_user_data(uid)
        msg = f"👤 **প্রোফাইল:**\n📛 নাম: {data['name']}\n💰 পয়েন্ট: {data['points']}\n🏦 ব্যাংক: {data['bank']}\n📅 জয়েন: {data['joined'][:10]}"
        bot.send_message(cid, msg)

    # --- সাব-মেনু কমান্ড ---
    # (AI)
    elif text == "🤖 এআই চ্যাট":
        user_temp_data[cid] = {'action': 'ai_chat'}
        bot.reply_to(message, "🤖 কিছু লিখুন:", reply_markup=get_cancel_menu())
    elif text == "🎨 এআই ছবি":
        user_temp_data[cid] = {'action': 'ai_image'}
        bot.reply_to(message, "🎨 কী আঁকতে চান? (English)", reply_markup=get_cancel_menu())
    elif text == "📝 পোস্ট মেকার":
        user_temp_data[cid] = {'action': 'post_maker'}
        bot.reply_to(message, "📝 বিষয় লিখুন:", reply_markup=get_cancel_menu())
    elif text == "🗣️ টেক্সট টু স্পিচ":
        user_temp_data[cid] = {'action': 'text_to_speech'}
        bot.reply_to(message, "🗣️ টেক্সট লিখুন:", reply_markup=get_cancel_menu())
    elif text == "✍️ বানান চেক":
        user_temp_data[cid] = {'action': 'spell_check'}
        bot.reply_to(message, "✍️ ভুল বানানটি লিখুন:", reply_markup=get_cancel_menu())
    elif text == "🖼️ OCR (ছবি->টেক্সট)":
        user_temp_data[cid] = {'action': 'ocr_scan'}
        bot.reply_to(message, "🖼️ ছবি পাঠান:", reply_markup=get_cancel_menu())

    # (Utility)
    elif text == "🖼️ ব্যাকগ্রাউন্ড রিমুভ":
        user_temp_data[cid] = {'action': 'remove_bg'}
        bot.reply_to(message, "🖼️ ছবি পাঠান:", reply_markup=get_cancel_menu())
    elif text == "🌤 লাইভ আবহাওয়া":
        user_temp_data[cid] = {'action': 'weather_check'}
        bot.reply_to(message, "🌤 শহরের নাম দিন:", reply_markup=get_cancel_menu())
    elif text == "📱 QR মেকার":
        user_temp_data[cid] = {'action': 'qr_make'}
        bot.reply_to(message, "📱 টেক্সট বা লিংক দিন:", reply_markup=get_cancel_menu())
    elif text == "📄 ছবি থেকে PDF":
        user_temp_data[cid] = {'action': 'img_to_pdf'}
        bot.reply_to(message, "📄 ছবি পাঠান:", reply_markup=get_cancel_menu())
    elif text == "📸 4K স্ক্রিনশট":
        user_temp_data[cid] = {'action': 'ss_web'}
        bot.reply_to(message, "🔗 ওয়েবসাইটের লিংক দিন:", reply_markup=get_cancel_menu())
    elif text == "🔗 ইউআরএল শর্টনার":
        user_temp_data[cid] = {'action': 'url_shorten'}
        bot.reply_to(message, "🔗 বড় লিংক দিন:", reply_markup=get_cancel_menu())
    elif text == "🔁 টেক্সট রিপিটার":
        user_temp_data[cid] = {'action': 'repeater_text'}
        bot.reply_to(message, "🔁 টেক্সট দিন:", reply_markup=get_cancel_menu())
    elif text == "🌐 অনুবাদক":
        user_temp_data[cid] = {'action': 'translator'}
        bot.reply_to(message, "🌐 টেক্সট দিন (যেকোনো ভাষা):", reply_markup=get_cancel_menu())
    elif text == "🕋 নামাজের সময়সূচি":
        user_temp_data[cid] = {'action': 'prayer_time'}
        bot.reply_to(message, "🕋 আপনার জেলা/শহরের নাম লিখুন (Example: Dhaka):", reply_markup=get_cancel_menu())

    # (Cyber)
    elif text == "🔐 Base64 টুল":
        user_temp_data[cid] = {'action': 'base64_tool'}
        bot.reply_to(message, "🔐 টেক্সট দিন:", reply_markup=get_cancel_menu())
    elif text == "💳 BIN চেকার":
        user_temp_data[cid] = {'action': 'bin_check'}
        bot.reply_to(message, "💳 BIN (First 6 digits):", reply_markup=get_cancel_menu())
    elif text == "💰 ক্রিপ্টো রেট":
        user_temp_data[cid] = {'action': 'crypto_rate'}
        bot.reply_to(message, "💰 কয়েন নাম (BTC, ETH):", reply_markup=get_cancel_menu())
    elif text == "✅ সাইট স্ট্যাটাস":
        user_temp_data[cid] = {'action': 'site_check'}
        bot.reply_to(message, "🔗 সাইট লিংক:", reply_markup=get_cancel_menu())
    
    # (Fun)
    elif text == "🎼 লিরিক্স ফাইন্ডার":
        user_temp_data[cid] = {'action': 'lyrics_find'}
        bot.reply_to(message, "🎼 গানের নাম:", reply_markup=get_cancel_menu())

    elif text == "❌ বাতিল করুন":
        if cid in user_temp_data: user_temp_data.pop(cid)
        bot.reply_to(message, "❌ অ্যাকশন বাতিল করা হয়েছে।", reply_markup=get_home_menu(uid))

# ================= বট রান করার কমান্ড =================
if __name__ == "__main__":
    # Flask সার্ভার একটি আলাদা থ্রেডে রান হবে (Render এর জন্য জরুরি)
    t = threading.Thread(target=run_web_server)
    t.start()
    
    # বট পোলিং শুরু
    print("🤖 Bot is Running...")
    bot.infinity_polling()
        
