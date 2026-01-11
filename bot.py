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

# ================= কনফিগারেশন =================
load_dotenv()

# Render বা লোকাল এনভায়রনমেন্ট থেকে টোকেন নেওয়া
API_TOKEN = os.getenv('BOT_TOKEN') 
if not API_TOKEN:
    API_TOKEN = 'YOUR_BOT_TOKEN_HERE' # এখানে আপনার টোকেনটি বসিয়ে দিন যদি .env না থাকে

ADMIN_ID = 6740599881 
BOT_USERNAME = "@HashtagMasterPro_Bot" 
FORCE_SUB_CHANNEL = "@ArifurHackworld" 
GAME_URL = "https://biplobc384-dotcom.github.io/gamezone" 

# ফাইল পাথ
DATA_FILE = "users.json"
CODES_FILE = "codes.json"

bot = telebot.TeleBot(API_TOKEN)
user_temp_data = {} 
file_lock = threading.Lock() 

# ================= Render Server (Keep Alive) =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Cyber Bot is Running Smoothly! 🚀"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ================= ডাটাবেস হেল্পার =================
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

# ইউজার ডাটা লোড এবং মিসিং ডাটা ফিক্স করা
def get_user_data(user_id):
    data = load_json(DATA_FILE)
    uid = str(user_id)
    if uid not in data: 
        data[uid] = {
            'name': 'Unknown', 
            'points': 50, 
            'bank': 0, 
            'joined': str(datetime.now()), 
            'streak': 0,
            'last_bonus': ''
        }
        save_json(DATA_FILE, data)
    
    # যদি পুরোনো ইউজারের নতুন কোনো ডাটা মিসিং থাকে তা ফিক্স করা হবে
    if 'streak' not in data[uid]: data[uid]['streak'] = 0
    if 'last_bonus' not in data[uid]: data[uid]['last_bonus'] = ''
    if 'bank' not in data[uid]: data[uid]['bank'] = 0
    save_json(DATA_FILE, data)
    
    return data[uid]

def update_points(user_id, amount):
    data = load_json(DATA_FILE)
    uid = str(user_id)
    if uid not in data: get_user_data(user_id) # ডাটা না থাকলে তৈরি করবে
    
    data[uid]['points'] = data[uid].get('points', 0) + amount
    save_json(DATA_FILE, data)
    return data[uid]['points']

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

# ================= মেনু কিবোর্ড =================
def get_home_menu(user_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🤖 এআই ও ক্রিয়েশন", "🛠 ইউটিলিটি টুলস")
    markup.add("💻 সাইবার ও টেক", "🎮 ফান ও গেমস") 
    markup.add("🏦 ব্যাংক ও লটারি", "👤 প্রোফাইল ও ব্যালেন্স") 
    if user_id == ADMIN_ID: markup.add("👑 অ্যাডমিন প্যানেল")
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

# ================= মেইন হ্যান্ডলার =================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    uid = message.from_user.id
    if not is_subscribed(uid):
        bot.send_message(message.chat.id, "⚠️ বটটি ব্যবহার করতে আমাদের চ্যানেলে জয়েন করুন!", reply_markup=get_sub_keyboard())
        return
    
    get_user_data(uid) # ইউজার চেক বা তৈরি
    bot.reply_to(message, "👋 **আসসালামু আলাইকুম!**\nCyber Bot 17.0 (Fixed Version)", parse_mode="Markdown", reply_markup=get_home_menu(uid))

# --- ওয়েব অ্যাপ ডাটা ---
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
        bot.send_message(message.chat.id, f"🎮 গেম আপডেট: নতুন ব্যালেন্স {new_balance}")
    except Exception as e: bot.send_message(message.chat.id, f"⚠️ Error: {e}")

# --- ফাইল আপলোড (ব্যাকআপ/রিস্টোর) ---
@bot.message_handler(content_types=['document'])
def handle_file_upload(message):
    cid = message.chat.id
    uid = message.from_user.id

    if uid == ADMIN_ID and cid in user_temp_data and user_temp_data[cid].get('action') == 'restore_db':
        try:
            file_name = message.document.file_name
            if file_name == "users.json":
                file_info = bot.get_file(message.document.file_id)
                downloaded_file = bot.download_file(file_info.file_path)

                with open(DATA_FILE, 'wb') as new_file:
                    new_file.write(downloaded_file)
                
                bot.reply_to(message, "✅ **ডাটাবেস রিস্টোর সফল হয়েছে!**", reply_markup=get_admin_menu())
                user_temp_data.pop(cid)
            else:
                bot.reply_to(message, "❌ ফাইলের নাম অবশ্যই `users.json` হতে হবে।")
        except Exception as e:
            bot.reply_to(message, f"❌ এরর: {e}")

# --- টেক্সট মেসেজ হ্যান্ডলার ---
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    cid = message.chat.id
    uid = message.from_user.id
    text = message.text

    # --- অ্যাডমিন কমান্ড ---
    if uid == ADMIN_ID:
        if "ব্যাকআপ" in text:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "rb") as file:
                    bot.send_document(cid, file, caption=f"💾 Backup: {datetime.now()}", visible_file_name="users.json")
            else: bot.reply_to(message, "⚠️ ফাইল নেই।")
            return

        elif "রিস্টোর" in text:
            user_temp_data[cid] = {'action': 'restore_db'}
            bot.reply_to(message, "📂 `users.json` ফাইলটি দিন:", reply_markup=get_cancel_menu())
            return
            
        elif "ব্রডকাস্ট" in text:
            user_temp_data[cid] = {'action': 'broadcast'}
            bot.reply_to(message, "📢 মেসেজ লিখুন:", reply_markup=get_cancel_menu())
            return

        elif "পয়েন্ট অ্যাড" in text:
            user_temp_data[cid] = {'action': 'admin_add_point_id'}
            bot.reply_to(message, "👤 User ID দিন:", reply_markup=get_cancel_menu())
            return

    # --- ইনপুট প্রসেসিং ---
    if cid in user_temp_data:
        action = user_temp_data[cid].get('action')
        
        if action == 'broadcast':
            data = load_json(DATA_FILE)
            c = 0
            bot.reply_to(message, "🚀 পাঠানো হচ্ছে...")
            for u in data:
                try: bot.send_message(u, f"📢 **নোটিশ:**\n\n{text}", parse_mode="Markdown"); c+=1
                except: pass
            bot.reply_to(message, f"✅ Sent to {c} users.", reply_markup=get_admin_menu())
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
                    f = BytesIO(res.encode())
                    f.name = "repeat.txt"
                    bot.send_document(cid, f, caption="✅ ফাইল রেডি।")
                else:
                    bot.reply_to(message, res)
            except: bot.reply_to(message, "❌ সংখ্যা দিন।")
            user_temp_data.pop(cid)
            return
            
        elif action == 'gift_id':
            user_temp_data[cid] = {'action': 'gift_amount', 'receiver': text}
            bot.reply_to(message, "💰 কত পয়েন্ট?", reply_markup=get_cancel_menu())
            return
        
        elif action == 'gift_amount':
            try:
                amt = int(text)
                rec = user_temp_data[cid]['receiver']
                if get_points(uid) >= amt and amt > 0:
                    update_points(uid, -amt)
                    update_points(rec, amt)
                    bot.reply_to(message, "✅ গিফট সফল।", reply_markup=get_home_menu(uid))
                else: bot.reply_to(message, "❌ ব্যালেন্স নেই।")
            except: bot.reply_to(message, "❌ এরর।")
            user_temp_data.pop(cid)
            return

        elif action == 'redeem_code':
            codes = load_codes()
            if text in codes and codes[text]['current_uses'] < codes[text]['max_uses']:
                update_points(uid, codes[text]['amount'])
                codes[text]['current_uses'] += 1
                save_codes(codes)
                bot.reply_to(message, f"🎉 +{codes[text]['amount']} পয়েন্ট!", reply_markup=get_home_menu(uid))
            else: bot.reply_to(message, "❌ ভুল কোড।")
            user_temp_data.pop(cid)
            return
        
        elif action == 'ai_chat':
            try:
                bot.send_chat_action(cid, 'typing')
                # সিম্পল Pollinations AI
                res = requests.get(f"https://text.pollinations.ai/{urllib.parse.quote('Reply in Bengali: '+text)}").text
                bot.reply_to(message, res, reply_markup=get_home_menu(uid))
            except: bot.reply_to(message, "⚠️ সার্ভার বিজি।")
            user_temp_data.pop(cid)
            return

    # --- ক্যানসেল ---
    if "বাতিল" in text:
        if cid in user_temp_data: user_temp_data.pop(cid)
        bot.reply_to(message, "🚫 বাতিল করা হয়েছে।", reply_markup=get_home_menu(uid))
        return

    # --- মেনু অ্যাকশন (Robust Matching) ---
    if "এআই" in text: 
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add("🤖 এআই চ্যাট", "🔙 মেইন মেনু")
        bot.send_message(cid, "🤖 **এআই জোন:**", reply_markup=markup)
        
    elif "ইউটিলিটি" in text: 
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add("🔁 টেক্সট রিপিটার", "🔙 মেইন মেনু")
        bot.send_message(cid, "🛠 **টুলস:**", reply_markup=markup)
        
    elif "সাইবার" in text: 
        bot.send_message(cid, "💻 **সাইবার জোন** শীঘ্রই আসছে!", reply_markup=get_home_menu(uid))
        
    elif "ফান" in text or "গেমস" in text: 
        user_points = get_points(uid)
        game_url_with_params = f"{GAME_URL}?points={user_points}"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        markup.add(types.KeyboardButton(text="🎮 প্লে গেম (Start)", web_app=types.WebAppInfo(url=game_url_with_params)))
        markup.add("🔙 মেইন মেনু")
        bot.send_message(cid, "🎡 **ফান জোন:**", reply_markup=markup)
        
    elif "ব্যাংক" in text: 
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add("📥 টাকা জমা (Deposit)", "📤 টাকা উত্তোলন (Withdraw)")
        markup.add("🔙 মেইন মেনু")
        bot.send_message(cid, "🏦 **সাইবার ব্যাংক:**", reply_markup=markup)
        
    elif "প্রোফাইল" in text:
        d = get_user_data(uid)
        msg = f"👤 **প্রোফাইল**\n📛 নাম: {d['name']}\n💰 পয়েন্ট: {d['points']}\n🏦 ব্যাংক: {d['bank']}\n🔥 স্ট্রিক: {d.get('streak', 0)}"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎁 বোনাস নিন", callback_data="daily_bonus"))
        markup.add(types.InlineKeyboardButton("🏆 লিডারবোর্ড", callback_data="leaderboard"))
        markup.add(types.InlineKeyboardButton("🔗 রেফার লিংক", callback_data="ref_link"), types.InlineKeyboardButton("🎟️ প্রোমো কোড", callback_data="promo_code"))
        markup.add(types.InlineKeyboardButton("💸 গিফট করুন", callback_data="gift_point"))
        
        bot.reply_to(message, msg, parse_mode="Markdown", reply_markup=markup)

    elif "মেইন মেনু" in text or "ব্যাক" in text:
        bot.send_message(cid, "🏠 মেইন মেনু:", reply_markup=get_home_menu(uid))

    elif "অ্যাডমিন প্যানেল" in text and uid == ADMIN_ID:
        bot.send_message(cid, "👑 প্যানেল", reply_markup=get_admin_menu())

    # --- ফিচার ট্রিগারস ---
    elif "টেক্সট রিপিটার" in text:
        user_temp_data[cid] = {'action': 'repeater_text'}
        bot.reply_to(message, "📝 টেক্সট লিখুন:", reply_markup=get_cancel_menu())
        
    elif "এআই চ্যাট" in text:
        user_temp_data[cid] = {'action': 'ai_chat'}
        bot.reply_to(message, "🤖 প্রশ্ন করুন:", reply_markup=get_cancel_menu())
        
    elif "টাকা জমা" in text:
        if get_points(uid) >= 100:
            update_points(uid, -100)
            d = load_json(DATA_FILE); d[str(uid)]['bank'] += 100; save_json(DATA_FILE, d)
            bot.reply_to(message, "✅ ১০০ পয়েন্ট জমা হলো।")
        else: bot.reply_to(message, "❌ ১০০ পয়েন্ট নেই।")

    elif "টাকা উত্তোলন" in text:
        d = get_user_data(uid)
        if d['bank'] >= 100:
            d['bank'] -= 100; d['points'] += 100; save_json(DATA_FILE, {'uid':d}) # Fixed save logic
            # Correct save logic below
            full_data = load_json(DATA_FILE)
            full_data[str(uid)]['bank'] -= 100
            full_data[str(uid)]['points'] += 100
            save_json(DATA_FILE, full_data)
            bot.reply_to(message, "✅ ১০০ পয়েন্ট তোলা হলো।")
        else: bot.reply_to(message, "❌ ব্যাংকে টাকা নেই।")

    elif "লটারি" in text and uid == ADMIN_ID:
        data = load_json(DATA_FILE)
        if data: bot.reply_to(message, f"🎉 বিজয়ী: {random.choice(list(data.keys()))}")

# ================= বাটন হ্যান্ডলার (Robust Version) =================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.message.chat.id
    data = call.data
    
    try:
        if data == "check_sub":
            if is_subscribed(uid):
                bot.delete_message(uid, call.message.message_id)
                bot.send_message(uid, "✅ ধন্যবাদ!", reply_markup=get_home_menu(uid))
            else: bot.answer_callback_query(call.id, "❌ জয়েন করেননি!", show_alert=True)
            
        elif data == "daily_bonus":
            d = load_json(DATA_FILE)
            u = d.get(str(uid), {})
            today = datetime.now().strftime("%Y-%m-%d")
            
            # ডাটা মিসিং হ্যান্ডলিং
            last_bonus = u.get('last_bonus', '')
            
            if last_bonus != today:
                u['points'] = u.get('points', 0) + 20
                u['last_bonus'] = today
                u['streak'] = u.get('streak', 0) + 1
                d[str(uid)] = u
                save_json(DATA_FILE, d)
                bot.answer_callback_query(call.id, "✅ +20 পয়েন্ট বোনাস!", show_alert=True)
                
                # ব্যালেন্স আপডেট দেখানো
                try:
                    new_text = f"👤 **প্রোফাইল**\n📛 নাম: {u['name']}\n💰 পয়েন্ট: {u['points']}\n🏦 ব্যাংক: {u['bank']}\n🔥 স্ট্রিক: {u['streak']}"
                    bot.edit_message_text(new_text, uid, call.message.message_id, parse_mode="Markdown", reply_markup=call.message.reply_markup)
                except: pass
            else: 
                bot.answer_callback_query(call.id, "⚠️ আজ বোনাস নিয়েছেন!", show_alert=True)

        elif data == "leaderboard":
            d = load_json(DATA_FILE)
            # পয়েন্ট অনুযায়ী সর্ট করা
            sorted_users = sorted(d.items(), key=lambda x: x[1].get('points', 0), reverse=True)[:10]
            msg = "🏆 **টপ ১০ লিডারবোর্ড**\n"
            for i, (k, v) in enumerate(sorted_users, 1): 
                msg += f"{i}. {v.get('name', 'User')} - {v.get('points', 0)}\n"
            bot.send_message(uid, msg)
            bot.answer_callback_query(call.id)

        elif data == "ref_link":
            link = f"https://t.me/{bot.get_me().username}?start={uid}"
            bot.send_message(uid, f"🔗 আপনার রেফার লিংক:\n{link}")
            bot.answer_callback_query(call.id)

        elif data == "promo_code":
            user_temp_data[uid] = {'action': 'redeem_code'}
            bot.send_message(uid, "🎟️ কোড দিন:", reply_markup=get_cancel_menu())
            bot.answer_callback_query(call.id)

        elif data == "gift_point":
            user_temp_data[uid] = {'action': 'gift_id'}
            bot.send_message(uid, "🎁 রিসিভার আইডি দিন:", reply_markup=get_cancel_menu())
            bot.answer_callback_query(call.id)

    except Exception as e:
        print(f"Callback Error: {e}")
        bot.answer_callback_query(call.id, "❌ এরর হয়েছে!", show_alert=True)

if __name__ == "__main__":
    t = threading.Thread(target=run_web_server)
    t.daemon = True
    t.start()
    print("Bot is running...")
    bot.infinity_polling()
    
