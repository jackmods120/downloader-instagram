# ╔══════════════════════════════════════════════════════════════════════════╗
# ║   ░░ ██╗███╗  ██╗███████╗████████╗ █████╗      ██████╗  ██████╗ ████████╗░░ ║
# ║   ░░ ██║████╗ ██║██╔════╝╚══██╔══╝██╔══██╗     ██╔══██╗██╔═══██╗╚══██╔══╝░░ ║
# ║   ░░ ██║██╔██╗██║███████╗   ██║   ███████║     ██████╔╝██║   ██║   ██║   ░░ ║
# ║   ░░ ██║██║╚████║╚════██║   ██║   ██╔══██║     ██╔══██╗██║   ██║   ██║   ░░ ║
# ║   ░░ ██║██║ ╚███║███████║   ██║   ██║  ██║     ██████╔╝╚██████╔╝   ██║   ░░ ║
# ║   ░░ ╚═╝╚═╝  ╚══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝     ╚═════╝  ╚═════╝    ╚═╝   ░░ ║
# ╠══════════════════════════════════════════════════════════════════════════╣
# ║  Version  : v1.0                                                         ║
# ║  Platform : Instagram Reels & Videos Downloader Bot                     ║
# ║  Stack    : FastAPI · python-telegram-bot · Firebase · Vercel           ║
# ╚══════════════════════════════════════════════════════════════════════════╝

import os, time, logging, httpx, re, html, asyncio, json, traceback
from datetime import datetime
from fastapi import FastAPI, Request
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, CallbackQueryHandler, filters,
)
from telegram.error import BadRequest

# ==============================================================================
# ── 1. CONFIGURATION ──────────────────────────────────────────────────────────
# ==============================================================================
TOKEN       = os.getenv("BOT_TOKEN") or "DUMMY_TOKEN"
DB_URL      = os.getenv("DB_URL") or ""
DB_SECRET   = os.getenv("DB_SECRET") or ""
OWNER_ID    = int(os.getenv("OWNER_ID") or "0")
DEV         = os.getenv("DEV_USERNAME") or "@YourUsername"
CHANNEL_URL = os.getenv("CHANNEL_URL") or "https://t.me/yourchannel"
START_TIME  = time.time()
SESSION_TTL = 1800

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)
app = FastAPI()

super_admins_set : set  = {OWNER_ID} if OWNER_ID else set()
admins_set       : set  = {OWNER_ID} if OWNER_ID else set()
channels_list    : list = []
blocked_set      : set  = set()
vip_set          : set  = set()
waiting_state    : dict = {}
last_cfg_load    = 0

CFG: dict = {
    "maintenance"  : False,
    "welcome_msg"  : "",
    "default_lang" : "ku",
    "api_timeout"  : 60,
    "vip_bypass"   : True,
    "admin_bypass" : True,
    "total_dl"     : 0,
    "total_users"  : 0,
}

# ==============================================================================
# ── 2. LANGUAGE DICTIONARY (Kurdish / English / Arabic) ───────────────────────
# ==============================================================================
L: dict = {

# ─────────────────────────────────── KURDISH ──────────────────────────────────
"ku": {
    "welcome"         : "👋 سڵاو {name} {badge}\n\n📸 بەخێربێیت بۆ بۆتی داگرتنی ئینستاگرام!\n🎬 ڤیدیۆ و ریلز بدابەزێنە بەبێ واتەرمارک.\n\n━━━━━━━━━━━━━━━━━━━\n👇 لینکی ئینستاگرامەکەت بنێرەم:",
    "help"            : "📚 ڕێنمایی بەکارهێنان\n\n1️⃣ لینکی ڤیدیۆ یان ریلز لە ئینستاگرام کۆپی بکە.\n2️⃣ لینکەکە لێرە پەیست بکە.\n3️⃣ ڤیدیۆکەت دەگات!\n\n✅ پشتگیریکراوەکان:\n• instagram.com/reel/...\n• instagram.com/p/...\n\n💎 VIP: بێ جۆینی ناچاری، خێرایی زۆرتر.\n📩 پەیوەندی: {dev}",
    "profile"         : "👤 کارتی پرۆفایل\n\n🆔 ئایدی: {id}\n👤 ناو: {name}\n🔗 یوزەرنەیم: @{user}\n📅 تۆماربوون: {date}\n💎 VIP: {vip}\n🌍 زمان: {ulang}\n📥 دابەزاندن: {dl} جار",
    "vip_info"        : "💎 تایبەتمەندییەکانی VIP\n\n✅ بەبێ جۆینی ناچاری.\n✅ خێرایی دابەزاندنی زیاتر.\n\nبۆ کڕینی VIP: {dev}",
    "lang_title"      : "🌍 زمانی خۆت هەڵبژێرە:",
    "lang_saved"      : "✅ زمانەکە گۆڕدرا!",
    "bot_lang_title"  : "🌍 زمانی سەرەکی بۆتەکە هەڵبژێرە:",
    "bot_lang_saved"  : "✅ زمانی سەرەکی بۆتەکە گۆڕدرا بۆ: {lang}",
    "force_join"      : "🔒 جۆینی ناچاری\nتکایە سەرەتا ئەم چەناڵانە جۆین بکە، پاشان کلیک لە '✅ جۆینم کرد' بکە:",
    "processing"      : "🔍 دەگەڕێم بۆ لینکەکە...\nچەند چرکەیەک چاوەڕێبە ⏳",
    "found"           : "✅ <b>ڤیدیۆکەت ئامادەیە!</b>\n\n📐 بەرز: {width}x{height}\n\n<i>دابەزاندرا بە بۆتی ئینستاگرام 📥</i>",
    "blocked_msg"     : "⛔ تۆ بلۆک کراویت.",
    "maintenance_msg" : "🛠 چاکسازی کاتی!\n\n⚙️ بۆتەکەمان لە ژێر نوێکردنەوەیەکی گەورەدایە.\n⏳ زووترین کاتێکدا دەگەڕێینەوە!\n\n📩 پەیوەندی: {dev}",
    "invalid_link"    : "❌ لینکەکە هەڵەیە یان ڤیدیۆکە گشتی نییە!\n\nدڵنیابە لینکەکە:\n• instagram.com/reel/...\n• instagram.com/p/...",
    "dl_fail"         : "❌ هەڵەیەک ڕوویدا! ناتوانرێت دابەزێنرێت.\nتکایە دووبارە هەوڵبدەرەوە.",
    "no_video"        : "❌ ڤیدیۆکە نەدۆزرایەوە! ئەم پۆستە ڤیدیۆی تێدا نییە.",
    "private_post"    : "🔒 ئەم پۆستە تایبەتییە!\nتەنیا پۆستی گشتی دادەگیرێت.",
    "invalid_id"      : "❌ ئایدیەکە دروست نییە! تەنیا ژمارە بنووسە.",
    "user_not_found"  : "⚠️ بەکارهێنەر نەدۆزرایەوە.",
    "broadcast_done"  : "📢 برۆدکاست تەواو بوو\n✅ گەیشت بە: {ok}\n❌ نەگەیشت: {fail}",
    "broadcast_sending": "📢 ئەرسال دەکرێت... ({done}/{total})",
    "welcome_set"     : "✅ نامەی بەخێرهاتن گۆڕدرا.",
    "write_welcome"   : "✍️ نامەی بەخێرهاتن بنووسە:\n(دەتوانیت {name} و {badge} بەکاربێنیت)",
    "write_id"        : "✍️ ئایدی کەسەکە بنووسە:",
    "write_ch"        : "✍️ یوزەرنەیمی چەناڵ بنووسە (نمونە: @mychannel):",
    "vip_yes"         : "بەڵێ 💎",
    "vip_no"          : "نەخێر",
    "badge_owner"     : "👑",
    "badge_super"     : "🌌",
    "badge_admin"     : "🛡",
    "badge_vip"       : "💎",
    "new_user_notify" : "👤 بەکارهێنەری نوێ!\n\n👤 ناو: {name}\n🔗 یوزەرنەیم: {uname}\n🆔 ئایدی: <code>{uid}</code>\n🌍 زمانی ئەپ: {app_lang}\n📅 کات: {date}",
    "b_notify_block"  : "🚫 بلۆک",
    "b_notify_vip"    : "💎 VIP بکە",
    "b_notify_admin"  : "🛡 ئەدمین بکە",
    "b_notify_info"   : "👤 زانیاری",
    "act_blocked"     : "✅ بلۆک کرا: {id}",
    "act_unblocked"   : "✅ بلۆک لادرا: {id}",
    "act_vip_added"   : "✅ VIP کرا: {id}",
    "act_vip_removed" : "✅ VIP لادرا: {id}",
    "act_adm_added"   : "✅ ئەدمین کرا: {id}",
    "act_sup_added"   : "✅ سوپەر ئەدمین کرا: {id}",
    "act_ch_wrong_fmt": "❌ فۆرماتی چەناڵ هەڵەیە! نمونە: @mychannel",
    "sup_ch_added"    : "✅ چەناڵ زیادکرا: {ch}",
    "userinfo_text"   : "👤 زانیاری بەکارهێنەر\n\n👤 ناو: {name}\n🔗 یوزەرنەیم: @{user}\n🆔 ئایدی: {id}\n💎 VIP: {vip}\n🌍 زمان: {lang}\n📥 دابەزاندن: {dl} جار\n📅 تۆماربوون: {date}",
    "b_dl"            : "📥 دابەزاندنی نوێ",
    "b_profile"       : "👤 پرۆفایلی من",
    "b_vip"           : "💎 بەشی VIP",
    "b_settings"      : "⚙️ ڕێکخستن و زمان",
    "b_help"          : "ℹ️ فێرکاری",
    "b_channel"       : "📢 کەناڵی بۆت",
    "b_panel"         : "⚙️ پانێڵی کۆنتڕۆڵ",
    "b_back"          : "🔙 گەڕانەوە",
    "b_ku"            : "🔴🔆🟢 کوردی",
    "b_en"            : "🇺🇸 English",
    "b_ar"            : "🇸🇦 العربية",
    "b_cancel"        : "❌ هەڵوەشاندنەوە",
    "b_joined"        : "✅ جۆینم کرد",
    "b_confirm_remove": "✅ بەڵێ، بیسڕەوە",
    "b_cancel_remove" : "❌ نەخێر",
    "unified_panel_title": "⚙️ پانێڵی کۆنتڕۆڵ\n\n👥 بەکارهێنەران: {users}\n💎 VIP: {vip}\n🚫 بلۆككراو: {blocked}\n📥 داونلۆد: {dl}\n⏱ Uptime: {uptime}",
    "adm_panel_title" : "🛡 بەشی ئەدمین",
    "adm_stats_title" : "📊 ئامارەکان:\n👥 کۆی بەکارهێنەران: {users}\n💎 VIP: {vip}\n🚫 بلۆككراو: {blocked}\n📥 داونلۆدەکان: {dl}\n⏱ Uptime: {uptime}",
    "adm_broadcast_ask": "✍️ پەیامەکەت بنێرە (تێکست، وێنە، ڤیدیۆ):",
    "adm_block_ask"   : "🚫 بلۆككردنی بەکارهێنەر:\n\n✍️ ئایدی بنووسە:",
    "adm_info_ask"    : "👤 زانیاری بەکارهێنەر:\n\n✍️ ئایدی بنووسە:",
    "b_adm_stats"     : "📊 ئامارەکان",
    "b_adm_broadcast" : "📢 برۆدکاست",
    "b_adm_block"     : "🚫 بلۆككردن",
    "b_adm_info"      : "👤 زانیاری کەس",
    "b_adm_admins"    : "👮 ئەدمینەکان",
    "sup_panel_title" : "🌌 بەشی سوپەر",
    "sup_maint_on"    : "🔴 چالاکە",
    "sup_maint_off"   : "🟢 ناچالاکە",
    "sup_admins_title": "👮 ئەدمینەکان ({count}):",
    "sup_vip_title"   : "💎 VIP ({count}):",
    "sup_ch_title"    : "📢 چەناڵەکان ({count}):",
    "sup_ch_empty"    : "📭 بەتاڵە",
    "confirm_remove_admin": "⚠️ دڵنیایت دەتەوێت ئەم ئەدمینە بسڕیتەوە؟\n🆔 {id}",
    "confirm_remove_super": "⚠️ دڵنیایت دەتەوێت ئەم سوپەر ئەدمینە بسڕیتەوە؟\n🆔 {id}",
    "confirm_remove_ch"   : "⚠️ دڵنیایت دەتەوێت ئەم چەناڵە بسڕیتەوە؟\n{ch}",
    "b_sup_maint"     : "🛠 چاکسازی",
    "b_sup_admins"    : "👮 ئەدمینەکان",
    "b_sup_supers"    : "🌌 سوپەر ئەدمینەکان",
    "b_sup_vip"       : "💎 VIPەکان",
    "b_sup_channels"  : "📢 چەناڵەکان",
    "b_sup_welcome"   : "✏️ نامەی بەخێرهاتن",
    "b_sup_bot_lang"  : "🌍 زمانی بۆت",
    "b_add"           : "➕ زیادکردن",
    "b_remove"        : "➖ سڕینەوە",
},

# ─────────────────────────────────── ENGLISH ──────────────────────────────────
"en": {
    "welcome"         : "👋 Hello {name} {badge}\n\n📸 Welcome to Instagram Downloader Bot!\n🎬 Download videos and Reels without watermark.\n\n━━━━━━━━━━━━━━━━━━━\n👇 Send me an Instagram link:",
    "help"            : "📚 How to Use\n\n1️⃣ Copy an Instagram video or Reel link.\n2️⃣ Paste it here.\n3️⃣ Get your video!\n\n✅ Supported:\n• instagram.com/reel/...\n• instagram.com/p/...\n\n💎 VIP: No forced join, faster downloads.\n📩 Contact: {dev}",
    "profile"         : "👤 Profile Card\n\n🆔 ID: {id}\n👤 Name: {name}\n🔗 Username: @{user}\n📅 Joined: {date}\n💎 VIP: {vip}\n🌍 Language: {ulang}\n📥 Downloads: {dl}",
    "vip_info"        : "💎 VIP Benefits\n\n✅ Skip forced channel joins.\n✅ Faster download speed.\n\nBuy VIP: {dev}",
    "lang_title"      : "🌍 Choose your language:",
    "lang_saved"      : "✅ Language changed!",
    "bot_lang_title"  : "🌍 Choose the bot's default language:",
    "bot_lang_saved"  : "✅ Bot default language changed to: {lang}",
    "force_join"      : "🔒 Forced Join\nPlease join these channels first, then click '✅ Joined':",
    "processing"      : "🔍 Looking up the link...\nPlease wait ⏳",
    "found"           : "✅ <b>Your video is ready!</b>\n\n📐 Resolution: {width}x{height}\n\n<i>Downloaded via Instagram Bot 📥</i>",
    "blocked_msg"     : "⛔ You are blocked.",
    "maintenance_msg" : "🛠 Maintenance!\n\n⚙️ The bot is under a major update.\n⏳ We'll be back shortly!\n\n📩 Contact: {dev}",
    "invalid_link"    : "❌ Invalid link or the video is not public!\n\nMake sure the link is:\n• instagram.com/reel/...\n• instagram.com/p/...",
    "dl_fail"         : "❌ An error occurred! Could not download.\nPlease try again.",
    "no_video"        : "❌ Video not found! This post has no video.",
    "private_post"    : "🔒 This post is private!\nOnly public posts can be downloaded.",
    "invalid_id"      : "❌ Invalid ID! Numbers only.",
    "user_not_found"  : "⚠️ User not found.",
    "broadcast_done"  : "📢 Broadcast complete\n✅ Reached: {ok}\n❌ Failed: {fail}",
    "broadcast_sending": "📢 Sending... ({done}/{total})",
    "welcome_set"     : "✅ Welcome message updated.",
    "write_welcome"   : "✍️ Write the welcome message:\n(You can use {name} and {badge})",
    "write_id"        : "✍️ Send the user ID:",
    "write_ch"        : "✍️ Send channel username (e.g. @mychannel):",
    "vip_yes"         : "Yes 💎",
    "vip_no"          : "No",
    "badge_owner"     : "👑",
    "badge_super"     : "🌌",
    "badge_admin"     : "🛡",
    "badge_vip"       : "💎",
    "new_user_notify" : "👤 New User!\n\n👤 Name: {name}\n🔗 Username: {uname}\n🆔 ID: <code>{uid}</code>\n🌍 App lang: {app_lang}\n📅 Date: {date}",
    "b_notify_block"  : "🚫 Block",
    "b_notify_vip"    : "💎 Make VIP",
    "b_notify_admin"  : "🛡 Make Admin",
    "b_notify_info"   : "👤 Info",
    "act_blocked"     : "✅ Blocked: {id}",
    "act_unblocked"   : "✅ Unblocked: {id}",
    "act_vip_added"   : "✅ VIP added: {id}",
    "act_vip_removed" : "✅ VIP removed: {id}",
    "act_adm_added"   : "✅ Admin added: {id}",
    "act_sup_added"   : "✅ Super admin added: {id}",
    "act_ch_wrong_fmt": "❌ Wrong channel format! Example: @mychannel",
    "sup_ch_added"    : "✅ Channel added: {ch}",
    "userinfo_text"   : "👤 User Info\n\n👤 Name: {name}\n🔗 Username: @{user}\n🆔 ID: {id}\n💎 VIP: {vip}\n🌍 Language: {lang}\n📥 Downloads: {dl}\n📅 Joined: {date}",
    "b_dl"            : "📥 New Download",
    "b_profile"       : "👤 My Profile",
    "b_vip"           : "💎 VIP Section",
    "b_settings"      : "⚙️ Settings & Language",
    "b_help"          : "ℹ️ Help",
    "b_channel"       : "📢 Bot Channel",
    "b_panel"         : "⚙️ Control Panel",
    "b_back"          : "🔙 Back",
    "b_ku"            : "🔴🔆🟢 Kurdish",
    "b_en"            : "🇺🇸 English",
    "b_ar"            : "🇸🇦 Arabic",
    "b_cancel"        : "❌ Cancel",
    "b_joined"        : "✅ I Joined",
    "b_confirm_remove": "✅ Yes, Remove",
    "b_cancel_remove" : "❌ No",
    "unified_panel_title": "⚙️ Control Panel\n\n👥 Users: {users}\n💎 VIP: {vip}\n🚫 Blocked: {blocked}\n📥 Downloads: {dl}\n⏱ Uptime: {uptime}",
    "adm_panel_title" : "🛡 Admin Section",
    "adm_stats_title" : "📊 Stats:\n👥 Total users: {users}\n💎 VIP: {vip}\n🚫 Blocked: {blocked}\n📥 Downloads: {dl}\n⏱ Uptime: {uptime}",
    "adm_broadcast_ask": "✍️ Send your message (text, photo, video):",
    "adm_block_ask"   : "🚫 Block User:\n\n✍️ Send user ID:",
    "adm_info_ask"    : "👤 User Info:\n\n✍️ Send user ID:",
    "b_adm_stats"     : "📊 Stats",
    "b_adm_broadcast" : "📢 Broadcast",
    "b_adm_block"     : "🚫 Block",
    "b_adm_info"      : "👤 User Info",
    "b_adm_admins"    : "👮 Admins",
    "sup_panel_title" : "🌌 Super Section",
    "sup_maint_on"    : "🔴 Active",
    "sup_maint_off"   : "🟢 Inactive",
    "sup_admins_title": "👮 Admins ({count}):",
    "sup_vip_title"   : "💎 VIP ({count}):",
    "sup_ch_title"    : "📢 Channels ({count}):",
    "sup_ch_empty"    : "📭 Empty",
    "confirm_remove_admin": "⚠️ Remove this admin?\n🆔 {id}",
    "confirm_remove_super": "⚠️ Remove this super admin?\n🆔 {id}",
    "confirm_remove_ch"   : "⚠️ Remove this channel?\n{ch}",
    "b_sup_maint"     : "🛠 Maintenance",
    "b_sup_admins"    : "👮 Admins",
    "b_sup_supers"    : "🌌 Super Admins",
    "b_sup_vip"       : "💎 VIPs",
    "b_sup_channels"  : "📢 Channels",
    "b_sup_welcome"   : "✏️ Welcome Message",
    "b_sup_bot_lang"  : "🌍 Bot Language",
    "b_add"           : "➕ Add",
    "b_remove"        : "➖ Remove",
},

# ─────────────────────────────────── ARABIC ───────────────────────────────────
"ar": {
    "welcome"         : "👋 مرحباً {name} {badge}\n\n📸 أهلاً بك في بوت تنزيل انستغرام!\n🎬 حمّل الفيديوهات والريلز بدون علامة مائية.\n\n━━━━━━━━━━━━━━━━━━━\n👇 أرسل لي رابط انستغرام:",
    "help"            : "📚 كيفية الاستخدام\n\n1️⃣ انسخ رابط الفيديو أو الريل من انستغرام.\n2️⃣ الصق الرابط هنا.\n3️⃣ احصل على الفيديو!\n\n✅ الروابط المدعومة:\n• instagram.com/reel/...\n• instagram.com/p/...\n\n💎 VIP: بدون اشتراك إجباري، سرعة أعلى.\n📩 للتواصل: {dev}",
    "profile"         : "👤 بطاقة الملف الشخصي\n\n🆔 المعرف: {id}\n👤 الاسم: {name}\n🔗 اسم المستخدم: @{user}\n📅 تاريخ التسجيل: {date}\n💎 VIP: {vip}\n🌍 اللغة: {ulang}\n📥 التنزيلات: {dl}",
    "vip_info"        : "💎 مميزات VIP\n\n✅ تخطي الاشتراك الإجباري.\n✅ سرعة تنزيل أعلى.\n\nلشراء VIP: {dev}",
    "lang_title"      : "🌍 اختر لغتك:",
    "lang_saved"      : "✅ تم تغيير اللغة!",
    "bot_lang_title"  : "🌍 اختر اللغة الافتراضية للبوت:",
    "bot_lang_saved"  : "✅ تم تغيير اللغة الافتراضية إلى: {lang}",
    "force_join"      : "🔒 الاشتراك الإجباري\nيرجى الانضمام إلى هذه القنوات أولاً، ثم اضغط '✅ انضممت':",
    "processing"      : "🔍 جاري البحث عن الرابط...\nانتظر لحظة ⏳",
    "found"           : "✅ <b>الفيديو جاهز!</b>\n\n📐 الدقة: {width}x{height}\n\n<i>تم التنزيل عبر بوت انستغرام 📥</i>",
    "blocked_msg"     : "⛔ أنت محظور.",
    "maintenance_msg" : "🛠 صيانة!\n\n⚙️ البوت تحت تحديث كبير.\n⏳ سنعود قريباً!\n\n📩 للتواصل: {dev}",
    "invalid_link"    : "❌ الرابط غير صحيح أو الفيديو غير عام!\n\nتأكد من أن الرابط:\n• instagram.com/reel/...\n• instagram.com/p/...",
    "dl_fail"         : "❌ حدث خطأ! تعذر التنزيل.\nيرجى المحاولة مجدداً.",
    "no_video"        : "❌ لم يتم العثور على فيديو! هذا المنشور لا يحتوي على فيديو.",
    "private_post"    : "🔒 هذا المنشور خاص!\nلا يمكن تنزيل سوى المنشورات العامة.",
    "invalid_id"      : "❌ معرف غير صحيح! أرقام فقط.",
    "user_not_found"  : "⚠️ المستخدم غير موجود.",
    "broadcast_done"  : "📢 اكتمل الإرسال\n✅ تم الإرسال: {ok}\n❌ فشل: {fail}",
    "broadcast_sending": "📢 جاري الإرسال... ({done}/{total})",
    "welcome_set"     : "✅ تم تحديث رسالة الترحيب.",
    "write_welcome"   : "✍️ اكتب رسالة الترحيب:\n(يمكنك استخدام {name} و {badge})",
    "write_id"        : "✍️ أرسل معرف المستخدم:",
    "write_ch"        : "✍️ أرسل اسم القناة (مثال: @mychannel):",
    "vip_yes"         : "نعم 💎",
    "vip_no"          : "لا",
    "badge_owner"     : "👑",
    "badge_super"     : "🌌",
    "badge_admin"     : "🛡",
    "badge_vip"       : "💎",
    "new_user_notify" : "👤 مستخدم جديد!\n\n👤 الاسم: {name}\n🔗 المعرف: {uname}\n🆔 ID: <code>{uid}</code>\n🌍 لغة التطبيق: {app_lang}\n📅 التاريخ: {date}",
    "b_notify_block"  : "🚫 حظر",
    "b_notify_vip"    : "💎 VIP",
    "b_notify_admin"  : "🛡 مشرف",
    "b_notify_info"   : "👤 معلومات",
    "act_blocked"     : "✅ تم الحظر: {id}",
    "act_unblocked"   : "✅ تم رفع الحظر: {id}",
    "act_vip_added"   : "✅ تم إضافة VIP: {id}",
    "act_vip_removed" : "✅ تم إزالة VIP: {id}",
    "act_adm_added"   : "✅ تم إضافة مشرف: {id}",
    "act_sup_added"   : "✅ تم إضافة سوبر مشرف: {id}",
    "act_ch_wrong_fmt": "❌ صيغة القناة خاطئة! مثال: @mychannel",
    "sup_ch_added"    : "✅ تمت إضافة القناة: {ch}",
    "userinfo_text"   : "👤 معلومات المستخدم\n\n👤 الاسم: {name}\n🔗 المعرف: @{user}\n🆔 ID: {id}\n💎 VIP: {vip}\n🌍 اللغة: {lang}\n📥 تنزيلات: {dl}\n📅 تاريخ الانضمام: {date}",
    "b_dl"            : "📥 تنزيل جديد",
    "b_profile"       : "👤 ملفي الشخصي",
    "b_vip"           : "💎 قسم VIP",
    "b_settings"      : "⚙️ الإعدادات واللغة",
    "b_help"          : "ℹ️ مساعدة",
    "b_channel"       : "📢 قناة البوت",
    "b_panel"         : "⚙️ لوحة التحكم",
    "b_back"          : "🔙 رجوع",
    "b_ku"            : "🔴🔆🟢 كردي",
    "b_en"            : "🇺🇸 English",
    "b_ar"            : "🇸🇦 العربية",
    "b_cancel"        : "❌ إلغاء",
    "b_joined"        : "✅ انضممت",
    "b_confirm_remove": "✅ نعم، احذف",
    "b_cancel_remove" : "❌ لا",
    "unified_panel_title": "⚙️ لوحة التحكم\n\n👥 المستخدمون: {users}\n💎 VIP: {vip}\n🚫 المحظورون: {blocked}\n📥 التنزيلات: {dl}\n⏱ وقت التشغيل: {uptime}",
    "adm_panel_title" : "🛡 قسم المشرف",
    "adm_stats_title" : "📊 الإحصائيات:\n👥 إجمالي المستخدمين: {users}\n💎 VIP: {vip}\n🚫 المحظورون: {blocked}\n📥 التنزيلات: {dl}\n⏱ وقت التشغيل: {uptime}",
    "adm_broadcast_ask": "✍️ أرسل رسالتك (نص، صورة، فيديو):",
    "adm_block_ask"   : "🚫 حظر مستخدم:\n\n✍️ أرسل معرف المستخدم:",
    "adm_info_ask"    : "👤 معلومات المستخدم:\n\n✍️ أرسل معرف المستخدم:",
    "b_adm_stats"     : "📊 الإحصائيات",
    "b_adm_broadcast" : "📢 إرسال جماعي",
    "b_adm_block"     : "🚫 حظر",
    "b_adm_info"      : "👤 معلومات مستخدم",
    "b_adm_admins"    : "👮 المشرفون",
    "sup_panel_title" : "🌌 القسم الخاص",
    "sup_maint_on"    : "🔴 مفعل",
    "sup_maint_off"   : "🟢 معطل",
    "sup_admins_title": "👮 المشرفون ({count}):",
    "sup_vip_title"   : "💎 VIP ({count}):",
    "sup_ch_title"    : "📢 القنوات ({count}):",
    "sup_ch_empty"    : "📭 فارغ",
    "confirm_remove_admin": "⚠️ هل تريد حذف هذا المشرف؟\n🆔 {id}",
    "confirm_remove_super": "⚠️ هل تريد حذف هذا السوبر مشرف؟\n🆔 {id}",
    "confirm_remove_ch"   : "⚠️ هل تريد حذف هذه القناة؟\n{ch}",
    "b_sup_maint"     : "🛠 الصيانة",
    "b_sup_admins"    : "👮 المشرفون",
    "b_sup_supers"    : "🌌 السوبر مشرفون",
    "b_sup_vip"       : "💎 VIP",
    "b_sup_channels"  : "📢 القنوات",
    "b_sup_welcome"   : "✏️ رسالة الترحيب",
    "b_sup_bot_lang"  : "🌍 لغة البوت",
    "b_add"           : "➕ إضافة",
    "b_remove"        : "➖ حذف",
},
}

LANG_NAMES = {"ku": "کوردی", "en": "English", "ar": "العربية"}
DIV = "━━━━━━━━━━━━━━━━━━━"

# ==============================================================================
# ── 3. UTILS & DATABASE ───────────────────────────────────────────────────────
# ==============================================================================
def tx(lang: str, key: str, **kw) -> str:
    base = L.get(lang, L["ku"])
    text = base.get(key, L["ku"].get(key, key))
    try:    return text.format(**kw)
    except: return text

def clean_title(t: str) -> str:
    return re.sub(r'[\\/*?:"<>|#]', "", str(t))[:100].strip() or "No Title"

def fb(path: str) -> str:
    return f"{DB_URL}/{path}.json?auth={DB_SECRET}"

def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def fmt(n) -> str:
    try:
        n = int(n)
        if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
        if n >= 1_000:     return f"{n/1_000:.1f}K"
        return str(n)
    except: return str(n)

def uptime() -> str:
    d, r = divmod(int(time.time() - START_TIME), 86400)
    h, r = divmod(r, 3600); m, s = divmod(r, 60)
    return f"{d}d {h}h {m}m {s}s"

def back(lang, to="main_menu_render"):
    return [[InlineKeyboardButton(tx(lang, "b_back"), callback_data=to)]]

def is_owner(uid):   return OWNER_ID and uid == OWNER_ID
def is_super(uid):   return uid in super_admins_set or is_owner(uid)
def is_admin(uid):   return uid in admins_set or is_super(uid)
def is_vip(uid):     return uid in vip_set or is_super(uid)
def is_blocked(uid): return uid in blocked_set
def bypass_join(uid): return (CFG.get("vip_bypass") and is_vip(uid)) or (CFG.get("admin_bypass") and is_admin(uid))

async def db_get(path):
    if not DB_URL: return None
    async with httpx.AsyncClient(timeout=10) as c:
        try:
            r = await c.get(fb(path))
            if r.status_code == 200 and r.text != "null": return r.json()
        except: pass
    return None

async def db_put(path, data):
    if not DB_URL: return
    async with httpx.AsyncClient(timeout=10) as c:
        try: await c.put(fb(path), json=data)
        except: pass

async def load_cfg(force=False):
    global super_admins_set, admins_set, channels_list, blocked_set, vip_set, last_cfg_load
    if not force and (time.time() - last_cfg_load < 45): return
    d = await db_get("sys")
    if d:
        if OWNER_ID:
            super_admins_set = set(d.get("super_admins", [OWNER_ID]))
            admins_set       = set(d.get("admins",       [OWNER_ID]))
        else:
            super_admins_set = set(d.get("super_admins", []))
            admins_set       = set(d.get("admins",       []))
        channels_list = d.get("channels", [])
        blocked_set   = set(d.get("blocked", []))
        vip_set       = set(d.get("vips",    []))
        CFG.update(d.get("cfg", {}))
        last_cfg_load = time.time()

async def save_cfg():
    await db_put("sys", {
        "super_admins": list(super_admins_set),
        "admins":       list(admins_set),
        "channels":     channels_list,
        "blocked":      list(blocked_set),
        "vips":         list(vip_set),
        "cfg":          CFG,
    })

async def user_get(uid) -> dict | None:   return await db_get(f"users/{uid}")
async def user_put(uid, data):            await db_put(f"users/{uid}", data)
async def user_field(uid, field, val):    await db_put(f"users/{uid}/{field}", val)
async def user_exists(uid) -> bool:       return (await db_get(f"users/{uid}")) is not None
async def all_uids() -> list:             return [int(k) for k in (await db_get("users") or {}).keys()]

async def get_user_lang(uid: int) -> str:
    ud = await db_get(f"users/{uid}/lang")
    if ud and ud in L: return ud
    return CFG.get("default_lang", "ku")

async def get_user_display(uid: int) -> str:
    ud = await db_get(f"users/{uid}")
    if ud:
        name = ud.get("name", str(uid))
        username = ud.get("user", "")
        return f"{name} (@{username}) [{uid}]" if username else f"{name} [{uid}]"
    return str(uid)

async def check_join(uid, ctx) -> tuple[bool, list]:
    if not channels_list: return True, []
    missing = []
    for ch in channels_list:
        try:
            m = await ctx.bot.get_chat_member(ch, uid)
            from telegram.constants import ChatMemberStatus
            if m.status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED):
                missing.append(ch)
        except: missing.append(ch)
    return len(missing) == 0, missing

# ==============================================================================
# ── 4. INSTAGRAM SCRAPER ──────────────────────────────────────────────────────
# ==============================================================================
def get_post_id(url: str) -> str | None:
    post_re = re.compile(r"instagram\.com/p/([a-zA-Z0-9_-]+)")
    reel_re = re.compile(r"instagram\.com/reels?/([a-zA-Z0-9_-]+)")
    m = post_re.search(url) or reel_re.search(url)
    return m.group(1) if m else None

async def fetch_instagram(url: str) -> dict | None:
    post_id = get_post_id(url)
    if not post_id: return None
    timeout = int(CFG.get("api_timeout", 60))
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"}

    async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as c:

        # Method 1: Instagram GraphQL API (rich data — title, owner, stats)
        try:
            import urllib.parse, json as _json
            variables = _json.dumps({"shortcode": post_id, "fetch_comment_count": "null",
                "parent_comment_count": "null", "child_comment_count": "null",
                "fetch_like_count": "null", "fetch_tagged_user_count": "null",
                "fetch_preview_comment_count": "null", "has_threaded_comments": "false",
                "hoisted_comment_id": "null", "hoisted_reply_id": "null"})
            params = urllib.parse.urlencode({
                "av": "0", "__d": "www", "__user": "0", "__a": "1",
                "lsd": "AVqbxe3J_YA", "jazoest": "2957",
                "fb_api_caller_class": "RelayModern",
                "fb_api_req_friendly_name": "PolarisPostActionLoadPostQueryQuery",
                "variables": variables,
                "server_timestamps": "true",
                "doc_id": "10015901848480474",
            })
            r = await c.post("https://www.instagram.com/api/graphql",
                content=params.encode(),
                headers={**headers,
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-FB-LSD": "AVqbxe3J_YA",
                    "X-IG-App-ID": "936619743392459",
                })
            if r.status_code == 200:
                media = r.json().get("data", {}).get("xdt_shortcode_media", {})
                if media:
                    dims   = media.get("dimensions", {})
                    owner  = media.get("owner", {}).get("username", "")
                    edges  = media.get("edge_media_to_caption", {}).get("edges", [])
                    title  = edges[0].get("node", {}).get("text", "") if edges else ""
                    views    = media.get("video_view_count") or media.get("play_count") or 0
                    likes    = (media.get("edge_media_preview_like") or {}).get("count") or 0
                    comments = (media.get("edge_media_to_comment") or {}).get("count") or 0
                    # audio
                    audio_url = None
                    clips = media.get("clips_metadata") or {}
                    orig  = (clips.get("original_sound_info") or {})
                    if orig.get("progressive_download_url"):
                        audio_url = orig["progressive_download_url"]
                    if not audio_url:
                        asset = ((clips.get("music_info") or {}).get("music_asset_info") or {})
                        if asset.get("progressive_download_url"):
                            audio_url = asset["progressive_download_url"]
                    # video or carousel images
                    video_url = media.get("video_url") if media.get("is_video") else None
                    images = []
                    if media.get("edge_sidecar_to_children"):
                        for edge in media["edge_sidecar_to_children"].get("edges", []):
                            node = edge.get("node", {})
                            if node.get("is_video") and not video_url:
                                video_url = node.get("video_url")
                            elif not node.get("is_video"):
                                img = node.get("display_url")
                                if img: images.append(img)
                    elif not media.get("is_video"):
                        img = media.get("display_url")
                        if img: images.append(img)

                    if video_url or images:
                        return {
                            "video_url": video_url,
                            "images":    images,
                            "audio_url": audio_url,
                            "title":     clean_title(title) if title else "",
                            "owner":     owner,
                            "views":     views,
                            "likes":     likes,
                            "comments":  comments,
                            "width":     str(dims.get("width", "?")),
                            "height":    str(dims.get("height", "?")),
                        }
        except: pass

        # Method 2: og:video meta tag scraping (fallback — basic info only)
        try:
            r = await c.get(f"https://www.instagram.com/p/{post_id}/", headers={
                "User-Agent": "facebookexternalhit/1.1",
                "Accept-Language": "en-US,en;q=0.9",
            })
            if r.status_code == 200:
                video_match = re.search(r'<meta property="og:video" content="([^"]+)"', r.text)
                if video_match:
                    video_url = html.unescape(video_match.group(1))
                    w = re.search(r'<meta property="og:video:width" content="([^"]+)"', r.text)
                    h = re.search(r'<meta property="og:video:height" content="([^"]+)"', r.text)
                    # Try to get title and owner from og tags
                    t_m = re.search(r'<meta property="og:title" content="([^"]+)"', r.text)
                    raw_title = html.unescape(t_m.group(1)) if t_m else ""
                    # og:title format is usually "username on Instagram: caption"
                    owner, title = "", raw_title
                    if " on Instagram" in raw_title:
                        parts = raw_title.split(" on Instagram", 1)
                        owner = parts[0].strip()
                        cap_part = parts[1].lstrip(": ").strip().strip('"')
                        title = cap_part[:200] if cap_part else ""
                    return {
                        "video_url": video_url,
                        "images":    [],
                        "audio_url": None,
                        "title":     clean_title(title),
                        "owner":     owner,
                        "views":     0,
                        "likes":     0,
                        "comments":  0,
                        "width":     w.group(1) if w else "?",
                        "height":    h.group(1) if h else "?",
                    }
        except: pass

        # Method 3: Third-party API fallback
        try:
            r = await c.get(f"https://api.instadownloader.org/v1?url=https://www.instagram.com/p/{post_id}/")
            if r.status_code == 200:
                d = r.json()
                if d.get("video"):
                    return {
                        "video_url": d["video"], "images": [], "audio_url": None,
                        "title": "", "owner": "", "views": 0, "likes": 0, "comments": 0,
                        "width": "?", "height": "?",
                    }
        except: pass

    return None

# ==============================================================================
# ── 5. UI HELPERS ─────────────────────────────────────────────────────────────
# ==============================================================================
async def render_main_menu(uid: int, lang: str, name: str) -> tuple[str, InlineKeyboardMarkup]:
    badge = (
        tx(lang, "badge_owner") if is_owner(uid) else
        tx(lang, "badge_super") if is_super(uid) else
        tx(lang, "badge_admin") if is_admin(uid) else
        tx(lang, "badge_vip")   if is_vip(uid)   else ""
    )
    wm   = CFG.get("welcome_msg", "")
    text = (
        wm.replace("{name}", html.escape(name)).replace("{badge}", badge)
        if wm and not is_admin(uid)
        else tx(lang, "welcome", name=html.escape(name), badge=badge)
    )
    kb = [
        [InlineKeyboardButton(tx(lang, "b_dl"), callback_data="ask_link")],
        [InlineKeyboardButton(tx(lang, "b_profile"), callback_data="show_profile"),
         InlineKeyboardButton(tx(lang, "b_vip"),     callback_data="show_vip")],
        [InlineKeyboardButton(tx(lang, "b_settings"), callback_data="show_settings"),
         InlineKeyboardButton(tx(lang, "b_help"),     callback_data="show_help")],
        [InlineKeyboardButton(tx(lang, "b_channel"), url=CHANNEL_URL)],
    ]
    if is_admin(uid):
        kb.append([InlineKeyboardButton(tx(lang, "b_panel"), callback_data="panel_unified")])
    return text, InlineKeyboardMarkup(kb)

def lang_select_buttons() -> list:
    return [[
        InlineKeyboardButton(L["ku"]["b_ku"], callback_data="set_lang_ku"),
        InlineKeyboardButton(L["en"]["b_en"], callback_data="set_lang_en"),
        InlineKeyboardButton(L["ar"]["b_ar"], callback_data="set_lang_ar"),
    ]]

def bot_lang_select_buttons() -> list:
    return [[
        InlineKeyboardButton(L["ku"]["b_ku"], callback_data="set_bot_lang_ku"),
        InlineKeyboardButton(L["en"]["b_en"], callback_data="set_bot_lang_en"),
        InlineKeyboardButton(L["ar"]["b_ar"], callback_data="set_bot_lang_ar"),
    ]]

# ==============================================================================
# ── 6. HANDLERS ───────────────────────────────────────────────────────────────
# ==============================================================================
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    user = update.effective_user
    lang = await get_user_lang(uid)

    if is_blocked(uid): return
    if CFG["maintenance"] and not is_admin(uid):
        await update.message.reply_text(tx(lang, "maintenance_msg", dev=DEV)); return

    is_new = not await user_exists(uid)
    if is_new:
        CFG["total_users"] = CFG.get("total_users", 0) + 1
        await save_cfg()
        await user_put(uid, {
            "name": user.first_name,
            "user": user.username or "",
            "date": now_str(),
            "vip":  False,
            "dl":   0,
            "lang": CFG.get("default_lang", "ku"),
        })
        if OWNER_ID:
            uname = f"@{user.username}" if user.username else "—"
            notify_text = tx("ku", "new_user_notify",
                name=html.escape(user.first_name),
                uname=uname, uid=uid,
                app_lang=user.language_code or "—",
                date=now_str()
            )
            notify_kb = InlineKeyboardMarkup([[
                InlineKeyboardButton(tx("ku", "b_notify_block"), callback_data=f"quick_blk_{uid}"),
                InlineKeyboardButton(tx("ku", "b_notify_vip"),   callback_data=f"quick_vip_{uid}"),
            ], [
                InlineKeyboardButton(tx("ku", "b_notify_admin"), callback_data=f"quick_adm_{uid}"),
                InlineKeyboardButton(tx("ku", "b_notify_info"),  callback_data=f"quick_inf_{uid}"),
            ]])
            try: await ctx.bot.send_message(OWNER_ID, notify_text, parse_mode="HTML", reply_markup=notify_kb)
            except: pass

    ok_sub, missing = await check_join(uid, ctx)
    if not ok_sub and not bypass_join(uid):
        kb = [[InlineKeyboardButton(f"📢 {ch}", url=f"https://t.me/{ch.lstrip('@')}")] for ch in missing]
        kb.append([InlineKeyboardButton(tx(lang, "b_joined"), callback_data="check_join_btn")])
        await update.message.reply_text(tx(lang, "force_join"), reply_markup=InlineKeyboardMarkup(kb)); return

    text, markup = await render_main_menu(uid, lang, user.first_name)
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)

async def cmd_ping(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if is_owner(update.effective_user.id):
        await update.message.reply_text(f"✅ PONG!\n⏱ Uptime: {uptime()}")

# ── Callback Handler ───────────────────────────────────────────────────────────
async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    uid  = q.from_user.id
    lang = await get_user_lang(uid)
    data = q.data or ""
    await q.answer()

    # ── Quick actions from owner notification ──────────────────────────────────
    if data.startswith("quick_blk_"):
        tid = int(data.split("_")[2])
        blocked_set.add(tid); await save_cfg()
        await q.edit_message_reply_markup(reply_markup=None)
        await q.message.reply_text(tx("ku", "act_blocked", id=tid)); return
    if data.startswith("quick_vip_"):
        tid = int(data.split("_")[2])
        vip_set.add(tid); await user_field(tid, "vip", True); await save_cfg()
        await q.message.reply_text(tx("ku", "act_vip_added", id=tid)); return
    if data.startswith("quick_adm_"):
        tid = int(data.split("_")[2])
        admins_set.add(tid); await save_cfg()
        await q.message.reply_text(tx("ku", "act_adm_added", id=tid)); return
    if data.startswith("quick_inf_"):
        tid = int(data.split("_")[2])
        ud = await user_get(tid)
        if not ud: await q.message.reply_text(tx("ku", "user_not_found")); return
        vip_str  = tx("ku", "vip_yes") if ud.get("vip") else tx("ku", "vip_no")
        lang_str = LANG_NAMES.get(ud.get("lang", "—"), "—")
        await q.message.reply_text(tx("ku", "userinfo_text",
            name=ud.get("name","—"), user=ud.get("user","—"),
            id=tid, vip=vip_str, lang=lang_str,
            dl=ud.get("dl", 0), date=ud.get("date","—")
        )); return

    # ── Force join check ───────────────────────────────────────────────────────
    if data == "check_join_btn":
        ok_sub, missing = await check_join(uid, ctx)
        if ok_sub or bypass_join(uid):
            text, markup = await render_main_menu(uid, lang, q.from_user.first_name)
            try: await q.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
            except: await q.message.reply_text(text, parse_mode="HTML", reply_markup=markup)
        else:
            kb = [[InlineKeyboardButton(f"📢 {ch}", url=f"https://t.me/{ch.lstrip('@')}")] for ch in missing]
            kb.append([InlineKeyboardButton(tx(lang, "b_joined"), callback_data="check_join_btn")])
            try: await q.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(kb))
            except: pass
        return

    # ── Main menu ──────────────────────────────────────────────────────────────
    if data == "main_menu_render":
        text, markup = await render_main_menu(uid, lang, q.from_user.first_name)
        try: await q.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
        except: await q.message.reply_text(text, parse_mode="HTML", reply_markup=markup)
        return

    # ── Ask for link ───────────────────────────────────────────────────────────
    if data == "ask_link":
        kb = InlineKeyboardMarkup(back(lang))
        try: await q.edit_message_text(
            "📎 لینکی ئینستاگرامەکەت بنێرەم:\n\n<i>نمونە: https://www.instagram.com/reel/ABC123/</i>",
            parse_mode="HTML", reply_markup=kb)
        except: pass
        return

    # ── Profile ────────────────────────────────────────────────────────────────
    if data == "show_profile":
        ud = await user_get(uid) or {}
        vip_str  = tx(lang, "vip_yes") if ud.get("vip") else tx(lang, "vip_no")
        lang_str = LANG_NAMES.get(ud.get("lang", lang), lang)
        text = tx(lang, "profile",
            id=uid, name=html.escape(q.from_user.first_name),
            user=q.from_user.username or "—",
            date=ud.get("date", "—"), vip=vip_str,
            ulang=lang_str, dl=ud.get("dl", 0)
        )
        try: await q.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(back(lang)))
        except: pass
        return

    # ── VIP ────────────────────────────────────────────────────────────────────
    if data == "show_vip":
        try: await q.edit_message_text(tx(lang, "vip_info", dev=DEV),
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(back(lang)))
        except: pass
        return

    # ── Help ───────────────────────────────────────────────────────────────────
    if data == "show_help":
        try: await q.edit_message_text(tx(lang, "help", dev=DEV),
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(back(lang)))
        except: pass
        return

    # ── Settings ───────────────────────────────────────────────────────────────
    if data == "show_settings":
        kb = lang_select_buttons() + back(lang)
        try: await q.edit_message_text(tx(lang, "lang_title"),
            reply_markup=InlineKeyboardMarkup(kb))
        except: pass
        return

    if data.startswith("set_lang_"):
        chosen = data[9:]
        if chosen in L:
            await user_field(uid, "lang", chosen)
            lang = chosen
        text, markup = await render_main_menu(uid, lang, q.from_user.first_name)
        try: await q.edit_message_text(text, parse_mode="HTML", reply_markup=markup)
        except: pass
        return

    if data.startswith("set_bot_lang_"):
        if is_super(uid):
            chosen = data[13:]
            if chosen in L:
                CFG["default_lang"] = chosen
                await save_cfg()
                await q.answer(tx(lang, "bot_lang_saved", lang=LANG_NAMES.get(chosen, chosen)), show_alert=True)
        return

    # ── Unified Panel ──────────────────────────────────────────────────────────
    if data == "panel_unified":
        if not is_admin(uid): return
        all_u = await db_get("users") or {}
        vip_c = sum(1 for v in all_u.values() if isinstance(v, dict) and v.get("vip"))
        text = tx(lang, "unified_panel_title",
            users=CFG.get("total_users", len(all_u)),
            vip=vip_c, blocked=len(blocked_set),
            dl=CFG.get("total_dl", 0), uptime=uptime()
        )
        kb = []
        if is_admin(uid):
            kb += [
                [InlineKeyboardButton(tx(lang, "b_adm_stats"),     callback_data="adm_stats"),
                 InlineKeyboardButton(tx(lang, "b_adm_broadcast"), callback_data="adm_broadcast")],
                [InlineKeyboardButton(tx(lang, "b_adm_block"),     callback_data="adm_block"),
                 InlineKeyboardButton(tx(lang, "b_adm_info"),      callback_data="adm_info")],
            ]
        if is_super(uid):
            kb += [
                [InlineKeyboardButton(tx(lang, "sup_panel_title")[:20], callback_data="sup_panel")],
            ]
        kb += back(lang)
        try: await q.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))
        except: pass
        return

    # ── Admin actions ──────────────────────────────────────────────────────────
    if data == "adm_stats":
        if not is_admin(uid): return
        all_u = await db_get("users") or {}
        vip_c = sum(1 for v in all_u.values() if isinstance(v, dict) and v.get("vip"))
        text = tx(lang, "adm_stats_title",
            users=CFG.get("total_users", len(all_u)),
            vip=vip_c, blocked=len(blocked_set),
            dl=CFG.get("total_dl", 0), uptime=uptime()
        )
        try: await q.edit_message_text(text, parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(back(lang, "panel_unified")))
        except: pass
        return

    if data == "adm_broadcast":
        if not is_admin(uid): return
        waiting_state[uid] = "broadcast_text"
        try: await q.edit_message_text(tx(lang, "adm_broadcast_ask"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(tx(lang, "b_cancel"), callback_data="panel_unified")
            ]]))
        except: pass
        return

    if data == "adm_block":
        if not is_admin(uid): return
        waiting_state[uid] = "action_blk_add"
        try: await q.edit_message_text(tx(lang, "adm_block_ask"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(tx(lang, "b_cancel"), callback_data="panel_unified")
            ]]))
        except: pass
        return

    if data == "adm_info":
        if not is_admin(uid): return
        waiting_state[uid] = "action_info_check"
        try: await q.edit_message_text(tx(lang, "adm_info_ask"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(tx(lang, "b_cancel"), callback_data="panel_unified")
            ]]))
        except: pass
        return

    # ── Super Panel ────────────────────────────────────────────────────────────
    if data == "sup_panel":
        if not is_super(uid): return
        maint_status = tx(lang, "sup_maint_on") if CFG["maintenance"] else tx(lang, "sup_maint_off")
        kb = [
            [InlineKeyboardButton(f"🛠 {maint_status}", callback_data="sup_toggle_maint")],
            [InlineKeyboardButton(tx(lang, "b_sup_admins"),   callback_data="sup_list_admins"),
             InlineKeyboardButton(tx(lang, "b_sup_supers"),   callback_data="sup_list_supers")],
            [InlineKeyboardButton(tx(lang, "b_sup_vip"),      callback_data="sup_list_vip"),
             InlineKeyboardButton(tx(lang, "b_sup_channels"), callback_data="sup_list_channels")],
            [InlineKeyboardButton(tx(lang, "b_sup_welcome"),  callback_data="sup_set_welcome"),
             InlineKeyboardButton(tx(lang, "b_sup_bot_lang"), callback_data="sup_set_bot_lang")],
        ] + back(lang, "panel_unified")
        try: await q.edit_message_text(tx(lang, "sup_panel_title"),
            reply_markup=InlineKeyboardMarkup(kb))
        except: pass
        return

    if data == "sup_toggle_maint":
        if not is_super(uid): return
        CFG["maintenance"] = not CFG["maintenance"]
        await save_cfg()
        await q.answer(f"🛠 {'ON' if CFG['maintenance'] else 'OFF'}", show_alert=True)
        await on_callback(update, ctx)
        return

    if data == "sup_set_welcome":
        if not is_super(uid): return
        waiting_state[uid] = "set_welcome"
        try: await q.edit_message_text(tx(lang, "write_welcome"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(tx(lang, "b_cancel"), callback_data="sup_panel")
            ]]))
        except: pass
        return

    if data == "sup_set_bot_lang":
        if not is_super(uid): return
        kb = bot_lang_select_buttons() + back(lang, "sup_panel")
        try: await q.edit_message_text(tx(lang, "bot_lang_title"),
            reply_markup=InlineKeyboardMarkup(kb))
        except: pass
        return

    if data == "sup_list_channels":
        if not is_super(uid): return
        ch_text = "\n".join(channels_list) if channels_list else tx(lang, "sup_ch_empty")
        kb = [
            [InlineKeyboardButton(tx(lang, "b_add"),    callback_data="sup_add_ch"),
             InlineKeyboardButton(tx(lang, "b_remove"), callback_data="sup_rm_ch_menu")],
        ] + back(lang, "sup_panel")
        try: await q.edit_message_text(
            tx(lang, "sup_ch_title", count=len(channels_list)) + f"\n{ch_text}",
            reply_markup=InlineKeyboardMarkup(kb))
        except: pass
        return

    if data == "sup_add_ch":
        if not is_super(uid): return
        waiting_state[uid] = "action_add_ch"
        try: await q.edit_message_text(tx(lang, "write_ch"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(tx(lang, "b_cancel"), callback_data="sup_list_channels")
            ]]))
        except: pass
        return

    if data == "sup_list_admins":
        if not is_super(uid): return
        adm_list = [str(a) for a in admins_set if not is_super(a)]
        text = tx(lang, "sup_admins_title", count=len(adm_list)) + "\n" + "\n".join(adm_list) if adm_list else tx(lang, "sup_admins_title", count=0) + "\n—"
        kb = [
            [InlineKeyboardButton(tx(lang, "b_add"),    callback_data="sup_add_admin"),
             InlineKeyboardButton(tx(lang, "b_remove"), callback_data="sup_rm_admin")],
        ] + back(lang, "sup_panel")
        try: await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
        except: pass
        return

    if data == "sup_add_admin":
        if not is_super(uid): return
        waiting_state[uid] = "action_adm_add"
        try: await q.edit_message_text(tx(lang, "write_id"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(tx(lang, "b_cancel"), callback_data="sup_list_admins")
            ]]))
        except: pass
        return

    if data == "sup_rm_admin":
        if not is_super(uid): return
        waiting_state[uid] = "action_adm_rm"
        try: await q.edit_message_text(tx(lang, "write_id"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(tx(lang, "b_cancel"), callback_data="sup_list_admins")
            ]]))
        except: pass
        return

    if data == "sup_list_vip":
        if not is_super(uid): return
        vip_list = [str(v) for v in vip_set]
        text = tx(lang, "sup_vip_title", count=len(vip_list)) + "\n" + ("\n".join(vip_list) if vip_list else "—")
        kb = [
            [InlineKeyboardButton(tx(lang, "b_add"),    callback_data="sup_add_vip"),
             InlineKeyboardButton(tx(lang, "b_remove"), callback_data="sup_rm_vip")],
        ] + back(lang, "sup_panel")
        try: await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
        except: pass
        return

    if data == "sup_add_vip":
        if not is_super(uid): return
        waiting_state[uid] = "action_vip_add"
        try: await q.edit_message_text(tx(lang, "write_id"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(tx(lang, "b_cancel"), callback_data="sup_list_vip")
            ]]))
        except: pass
        return

    if data == "sup_rm_vip":
        if not is_super(uid): return
        waiting_state[uid] = "action_vip_rm"
        try: await q.edit_message_text(tx(lang, "write_id"),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(tx(lang, "b_cancel"), callback_data="sup_list_vip")
            ]]))
        except: pass
        return

# ── Message Handler ────────────────────────────────────────────────────────────
async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    uid  = update.effective_user.id
    msg  = update.message
    txt  = msg.text or ""
    lang = await get_user_lang(uid)

    # ── Waiting States ─────────────────────────────────────────────────────────
    if uid in waiting_state:
        state = waiting_state.pop(uid)

        if state == "set_welcome":
            CFG["welcome_msg"] = txt; await save_cfg()
            await msg.reply_text(tx(lang, "welcome_set")); return

        if state == "broadcast_text":
            all_u = await all_uids(); ok = fail = 0
            st = await msg.reply_text(tx(lang, "broadcast_sending", done=0, total=len(all_u)))
            for i, t in enumerate(all_u):
                try:
                    await ctx.bot.copy_message(chat_id=t, from_chat_id=msg.chat_id, message_id=msg.message_id)
                    ok += 1; await asyncio.sleep(0.04)
                except: fail += 1
                if i % 100 == 0 and i > 0:
                    try: await st.edit_text(tx(lang, "broadcast_sending", done=i, total=len(all_u)))
                    except: pass
            await st.edit_text(tx(lang, "broadcast_done", ok=ok, fail=fail)); return

        if state.startswith("action_"):
            action = state[len("action_"):]
            if action == "add_ch":
                ch = txt.strip()
                if not ch.startswith("@") or len(ch) < 3:
                    await msg.reply_text(tx(lang, "act_ch_wrong_fmt")); return
                if ch not in channels_list:
                    channels_list.append(ch); await save_cfg()
                await msg.reply_text(tx(lang, "sup_ch_added", ch=ch)); return

            if not txt.strip().isdigit():
                await msg.reply_text(tx(lang, "invalid_id")); return
            tid = int(txt.strip())

            if action == "blk_add":
                blocked_set.add(tid); await save_cfg()
                await msg.reply_text(tx(lang, "act_blocked", id=tid))
            elif action == "info_check":
                ud = await user_get(tid)
                if not ud: await msg.reply_text(tx(lang, "user_not_found")); return
                vip_str  = tx(lang, "vip_yes") if ud.get("vip") else tx(lang, "vip_no")
                lang_str = LANG_NAMES.get(ud.get("lang", "—"), "—")
                await msg.reply_text(tx(lang, "userinfo_text",
                    name=ud.get("name","—"), user=ud.get("user","—"),
                    id=tid, vip=vip_str, lang=lang_str,
                    dl=ud.get("dl", 0), date=ud.get("date","—")
                ))
            elif action == "adm_add":
                admins_set.add(tid); await save_cfg()
                await msg.reply_text(tx(lang, "act_adm_added", id=tid))
            elif action == "adm_rm":
                admins_set.discard(tid); await save_cfg()
                await msg.reply_text(f"✅ Admin removed: {tid}")
            elif action == "vip_add":
                vip_set.add(tid); await user_field(tid, "vip", True); await save_cfg()
                await msg.reply_text(tx(lang, "act_vip_added", id=tid))
            elif action == "vip_rm":
                vip_set.discard(tid); await user_field(tid, "vip", False); await save_cfg()
                await msg.reply_text(tx(lang, "act_vip_removed", id=tid))
            return

    # ── Instagram Link ─────────────────────────────────────────────────────────
    if is_blocked(uid): return
    if CFG["maintenance"] and not is_admin(uid):
        await msg.reply_text(tx(lang, "maintenance_msg", dev=DEV)); return

    is_insta = "instagram.com/reel" in txt or "instagram.com/p/" in txt
    if not is_insta: return

    ok_sub, missing = await check_join(uid, ctx)
    if not ok_sub and not bypass_join(uid):
        kb = [[InlineKeyboardButton(f"📢 {ch}", url=f"https://t.me/{ch.lstrip('@')}")] for ch in missing]
        kb.append([InlineKeyboardButton(tx(lang, "b_joined"), callback_data="check_join_btn")])
        await msg.reply_text(tx(lang, "force_join"), reply_markup=InlineKeyboardMarkup(kb)); return

    # Progress animation
    frames = ["⬜⬜⬜⬜⬜", "⬛⬜⬜⬜⬜", "⬛⬛⬜⬜⬜", "⬛⬛⬛⬜⬜", "⬛⬛⬛⬛⬜", "⬛⬛⬛⬛⬛"]
    status = await msg.reply_text(f"🔍 {frames[0]}")

    async def animated_progress():
        for frame in frames[1:]:
            try: await status.edit_text(f"🔍 {frame}")
            except: pass
            await asyncio.sleep(0.4)

    progress_task = asyncio.create_task(animated_progress())

    try:
        data = await fetch_instagram(txt)
        progress_task.cancel()

        if not data:
            await status.edit_text(tx(lang, "invalid_link")); return

        video_url = data.get("video_url")
        if not video_url:
            await status.edit_text(tx(lang, "no_video")); return

        try: await status.delete()
        except: pass

        # Caption with stats
        if data.get("title") or data.get("owner"):
            caption = (
                f"📝 {html.escape(data.get('title',''))}\n"
                f"👤 {html.escape(data.get('owner',''))}\n\n"
                f"📊 ئامارەکان:\n"
                f"👁 بینەر: {fmt(data.get('views',0))}  \n"
                f"❤️ لایک: {fmt(data.get('likes',0))}  \n"
                f"💬 کۆمێنت: {fmt(data.get('comments',0))}\n\n"
                f"🎬 <a href='https://t.me/Instagram_Downloader_Jack_Robot'>کلیک لێرە بکە — دابەزاندن دەستپێبکە</a>"
            )
        else:
            caption = tx(lang, "found", width=data.get("width","?"), height=data.get("height","?"))

        try:
            await ctx.bot.send_video(uid, video_url, caption=caption, parse_mode="HTML")
        except Exception:
            await ctx.bot.send_message(uid,
                f"{caption}\n\n📥 <a href='{video_url}'>لینکی ڤیدیۆ — کلیک بکە دابەزێنرێت</a>",
                parse_mode="HTML")

        CFG["total_dl"] = CFG.get("total_dl", 0) + 1
        await save_cfg()
        ud = await user_get(uid) or {}
        await user_field(uid, "dl", ud.get("dl", 0) + 1)

    except Exception as e:
        progress_task.cancel()
        log.error(f"Instagram Download Error: {traceback.format_exc()}")
        try: await status.edit_text(tx(lang, "dl_fail"))
        except: pass

# ==============================================================================
# ── 7. FASTAPI ROUTES ─────────────────────────────────────────────────────────
# ==============================================================================
_token = TOKEN if TOKEN != "DUMMY_TOKEN" else "123456:ABC"
ptb = ApplicationBuilder().token(_token).build()
ptb.add_handler(CommandHandler(["start", "menu"], cmd_start))
ptb.add_handler(CommandHandler("ping", cmd_ping))
ptb.add_handler(CallbackQueryHandler(on_callback))
ptb.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, on_message))

@app.post("/api/main")
async def webhook(req: Request):
    if TOKEN == "DUMMY_TOKEN" or not TOKEN:
        return {"ok": False, "error": "BOT_TOKEN IS MISSING"}
    try:
        body = await req.json()
        if not ptb.running: await ptb.initialize()
        await load_cfg(force=False)
        await ptb.process_update(Update.de_json(body, ptb.bot))
        return {"ok": True}
    except Exception as e:
        log.error(f"WEBHOOK ERROR: {traceback.format_exc()}")
        try:
            if OWNER_ID:
                await ptb.bot.send_message(OWNER_ID,
                    f"⚠️ Critical Error:\n\n{html.escape(str(e))}", parse_mode="HTML")
        except: pass
        return {"ok": False, "error": str(e)}

@app.get("/api/main")
async def health_check():
    t = "✅ Set" if TOKEN and TOKEN != "DUMMY_TOKEN" else "❌ Missing"
    d = "✅ Set" if DB_URL    else "❌ Missing (Firebase optional)"
    o = "✅ Set" if OWNER_ID  else "❌ Missing"
    return {
        "status": "running",
        "bot_token": t,
        "firebase": d,
        "owner_id": o,
        "uptime": uptime(),
    }

# REST API endpoint for direct use (website / other bots)
@app.get("/api/video")
async def get_video(postUrl: str = ""):
    if not postUrl:
        return {"ok": False, "error": "postUrl parameter is required"}
    data = await fetch_instagram(postUrl)
    if not data:
        return {"ok": False, "error": "Could not fetch video. Post may be private or invalid."}
    return {"ok": True, "data": data}
