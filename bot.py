import telebot
from telebot import types
import json
import os
import random
import requests
import urllib.parse
import threading
from datetime import datetime, timedelta
from io import BytesIO
from flask import Flask
from dotenv import load_dotenv

# ================= কনফিগারেশন (SECURE) =================
# .env ফাইল থেকে টোকেন লোড করা হচ্ছে
load_dotenv()

# প্রথমে এনভায়রনমেন্ট থেকে টোকেন খুঁজবে, না পেলে হার্ডকোডেড স্ট্রিং (নিরাপত্তার জন্য এনভায়রনমেন্ট ব্যবহার করুন)
API_TOKEN = os.getenv('BOT_TOKEN') 

if not API_TOKEN:
    print("❌ Error: BOT_TOKEN not found! Please set it in .env file or Environment Variables.")
    # টেস্টিং এর জন্য আপনার টোকেন এখানে রাখতে পারেন, তবে প্রোডাকশনে সরিয়ে ফেলা ভালো
    API_TOKEN = 'YOUR_BOT_TOKEN_HERE' 

ADMIN_ID = 6740599881 
BOT_USERNAME = "@HashtagMasterPro_Bot" 
FORCE_SUB_CHANNEL = "@ArifurHackworld" 
GAME_URL = "https://biplobc384-dotcom.github.io/gamezone" 

# ফাইল পাথ
DATA_FILE = "users.json"
CODES_FILE = "codes.json"
CONFIG_FILE = "config.json" 

bot = telebot.TeleBot(API_TOKEN)
user_temp_data = {} 
chat_queue = [] 
file_lock = threading.Lock() 

# ================= Render Web Server =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Cyber Bot is Running Securely! 🛡️"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ================= ডাটাবেস ইউটিলিটি =================
def load_json(filename):
    if not os.path.exists(filename): return {}
    with open(filename, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

def save_json(filename, data):
    with file_lock:
        with open(filename, 'w', encoding='utf-8') as f: 
            json.dump(data, f, indent=4, ensure_ascii=False)

def get_user_data(user_id):
    data = load_json(DATA_FILE)
    uid = str(user_id)
    if uid not in data: 
        data[uid] = {'name': 'Unknown', 'points': 50, 'bank': 0, 'joined': str(datetime.now())}
        save_json(DATA_FILE, data)
    return data[uid]

def update_points(user_id, amount):
    data = load_json(DATA_FILE)
    uid = str(user_id)
    if uid not in data: data[uid] = {'points': 50, 'name': 'Unknown', 'bank': 0} 
    data[uid]['points'] = data[uid].get('points', 0) + amount
    save_json(DATA_FILE, data)
    return data[uid]['points']

def get_points(user_id):
    data = load_json(DATA_FILE)
    return data.get(str(user_id), {}).get('points', 0)

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

# ================= মেনু সিস্টেম =================
def get_home_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🤖 এআই ও ক্রিয়েশন", "🛠 ইউটিলিটি টুলস")
    markup.add("💻 সাইবার ও টেক", "🎮 ফান ও গেমস") 
    markup.add("🏦 ব্যাংক ও লটারি", "👤 প্রোফাইল ও ব্যালেন্স") 
    if user_id == ADMIN_ID: markup.add("👑 অ্যাডমিন প্যানেল")
    return markup

def get_admin_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("💾 ব্যাকআপ", "📂 রিস্টোর")  # নতুন বাটন
    markup.add("📢 ব্রডকাস্ট", "➕ পয়েন্ট অ্যাড")
    markup.add("🎲 লটারি ড্র", "🔙 মেইন মেনু") 
    return markup

def get_cancel_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("❌ বাতিল করুন")
    return markup

# ================= হ্যান্ডলারস =================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.from_user.id
    if not is_subscribed(uid):
        bot.send_message(message.chat.id, "⚠️ বটটি ব্যবহার করতে আমাদের চ্যানেলে জয়েন করুন!", reply_markup=get_sub_keyboard())
        return
    
    # ইউজার রেজিস্ট্রেশন
    data = load_json(DATA_FILE)
    if str(uid) not in data:
        data[str(uid)] = {'name': message.from_user.first_name, 'points': 50, 'bank': 0, 'joined': str(datetime.now())}
        save_json(DATA_FILE, data)

    bot.reply_to(message, "👋 **আসসালামু আলাইকুম!**\nCyber Bot 16.0 (Secure & Backup Ready)", parse_mode="Markdown", reply_markup=get_home_menu(uid))

@bot.message_handler(func=lambda m: m.text == "👑 অ্যাডমিন প্যানেল")
def admin_panel_handler(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "👑 **অ্যাডমিন প্যানেল**\nযেকোনো অপশন সিলেক্ট করুন:", reply_markup=get_admin_menu())

@bot.message_handler(func=lambda m: m.text == "🔙 মেইন মেনু")
def back_home(message):
    bot.reply_to(message, "🏠 মেইন মেনু:", reply_markup=get_home_menu(message.from_user.id))

# ================= ব্যাকআপ ও রিস্টোর ফিচার =================

@bot.message_handler(content_types=['document'])
def handle_file_upload(message):
    cid = message.chat.id
    uid = message.from_user.id

    # রিস্টোর মোড চেক করা
    if uid == ADMIN_ID and cid in user_temp_data and user_temp_data[cid].get('action') == 'restore_db':
        try:
            file_name = message.document.file_name
            if file_name == "users.json":
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)

                with open(DATA_FILE, 'wb') as new_file:
                    new_file.write(downloaded_file)
                
                bot.reply_to(message, "✅ **ডাটাবেস রিস্টোর সফল হয়েছে!**\nএখন নতুন ডাটা ব্যবহার করা হবে।", reply_markup=get_admin_menu())
                user_temp_data.pop(cid)
            else:
                bot.reply_to(message, "❌ ভুল ফাইল! ফাইলের নাম অবশ্যই `users.json` হতে হবে।")
        except Exception as e:
            bot.reply_to(message, f"❌ এরর: {e}")

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    cid = message.chat.id
    uid = message.from_user.id
    text = message.text

    # --- অ্যাডমিন অ্যাকশনস ---
    if uid == ADMIN_ID:
        if text == "💾 ব্যাকআপ":
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "rb") as file:
                    caption = f"💾 **Database Backup**\n📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    bot.send_document(cid, file, caption=caption, visible_file_name="users.json")
            else:
                bot.reply_to(message, "⚠️ ডাটাবেস ফাইল পাওয়া যায়নি।")
            return

        elif text == "📂 রিস্টোর":
            user_temp_data[cid] = {'action': 'restore_db'}
            bot.reply_to(message, "📂 অনুগ্রহ করে আপনার `users.json` ব্যাকআপ ফাইলটি এখানে আপলোড করুন:", reply_markup=get_cancel_menu())
            return
            
        elif text == "📢 ব্রডকাস্ট":
            user_temp_data[cid] = {'action': 'broadcast'}
            bot.reply_to(message, "📢 মেসেজ লিখুন:", reply_markup=get_cancel_menu())
            return

    # --- ক্যানসেল ---
    if text == "❌ বাতিল করুন":
        if cid in user_temp_data: user_temp_data.pop(cid)
        bot.reply_to(message, "🚫 অ্যাকশন বাতিল করা হয়েছে।", reply_markup=get_home_menu(uid))
        return

    # --- ব্রডকাস্ট লজিক ---
    if cid in user_temp_data and user_temp_data[cid].get('action') == 'broadcast':
        data = load_json(DATA_FILE)
        count = 0
        bot.reply_to(message, "🚀 পাঠানো হচ্ছে...")
        for user in data:
            try:
                bot.send_message(user, f"📢 **নোটিশ:**\n\n{text}", parse_mode="Markdown")
                count += 1
            except: pass
        bot.reply_to(message, f"✅ সফলভাবে {count} জন ইউজারকে পাঠানো হয়েছে।", reply_markup=get_admin_menu())
        user_temp_data.pop(cid)
        return

    # --- সাধারণ মেনু ---
    if text == "👤 প্রোফাইল ও ব্যালেন্স":
        d = get_user_data(uid)
        bot.reply_to(message, f"👤 **{d['name']}**\n💰 পয়েন্ট: {d['points']}\n🏦 ব্যাংক: {d['bank']}", reply_markup=get_home_menu(uid))

    elif text == "🎲 লটারি ড্র" and uid == ADMIN_ID:
         # সিম্পল লটারি ড্র লজিক
        data = load_json(DATA_FILE)
        if data:
            winner = random.choice(list(data.keys()))
            bot.reply_to(message, f"🎉 বিজয়ী: `{winner}`")
        else:
             bot.reply_to(message, "কোনো ইউজার নেই।")

if __name__ == "__main__":
    t = threading.Thread(target=run_web_server)
    t.daemon = True
    t.start()
    print("Bot is running...")
    bot.infinity_polling()
    
