# ╔══════════════════════════════════════════════════════════════════════════╗
# ║   ░░ ██╗███╗  ██╗███████╗████████╗ █████╗      ██████╗  ██████╗ ████████╗░░ ║
# ║   ░░ ██║████╗ ██║██╔════╝╚══██╔══╝██╔══██╗     ██╔══██╗██╔═══██╗╚══██╔══╝░░ ║
# ║   ░░ ██║██╔██╗██║███████╗   ██║   ███████║     ██████╔╝██║   ██║   ██║   ░░ ║
# ║   ░░ ██║██║╚████║╚════██║   ██║   ██╔══██║     ██╔══██╗██║   ██║   ██║   ░░ ║
# ║   ░░ ██║██║ ╚███║███████║   ██║   ██║  ██║     ██████╔╝╚██████╔╝   ██║   ░░ ║
# ║   ░░ ╚═╝╚═╝  ╚══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝     ╚═════╝  ╚═════╝    ╚═╝   ░░ ║
# ╠══════════════════════════════════════════════════════════════════════════╣
# ║  Version  : v2.0                                                         ║
# ║  Platform : Instagram Reels & Videos Downloader Bot                     ║
# ║  Stack    : FastAPI · python-telegram-bot · Firebase · Vercel           ║
# ╚══════════════════════════════════════════════════════════════════════════╝

import os, time, logging, io, httpx, re, html, asyncio, json, traceback
from datetime import datetime
from fastapi import FastAPI, Request
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    InputMediaPhoto, ForceReply
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
    "welcome"              : "👋 سڵاو {name} {badge}\n\n📸 بەخێربێیت بۆ بۆتی داگرتنی ئینستاگرام!\n🎬 ڤیدیۆ و ریلز بدابەزێنە بەبێ واتەرمارک.\n\n━━━━━━━━━━━━━━━━━━━\n👇 لینکی ئینستاگرامەکەت بنێرەم:",
    "help"                 : "📚 ڕێنمایی بەکارهێنان\n\n1️⃣ لینکی ڤیدیۆ یان ریلز لە ئینستاگرام کۆپی بکە.\n2️⃣ لینکەکە لێرە پەیست بکە.\n3️⃣ ڤیدیۆکەت دەگات!\n\n✅ پشتگیریکراوەکان:\n• instagram.com/reel/...\n• instagram.com/p/...\n\n💎 VIP: بێ جۆینی ناچاری، خێرایی زۆرتر.\n📩 پەیوەندی: {dev}",
    "profile"              : "👤 کارتی پرۆفایل\n\n🆔 ئایدی: {id}\n👤 ناو: {name}\n🔗 یوزەرنەیم: @{user}\n📅 تۆماربوون: {date}\n💎 VIP: {vip}\n🌍 زمان: {ulang}\n📥 دابەزاندن: {dl} جار",
    "vip_info"             : "💎 تایبەتمەندییەکانی VIP\n\n✅ بەبێ جۆینی ناچاری.\n✅ خێرایی دابەزاندنی زیاتر.\n\nبۆ کڕینی VIP: {dev}",
    "lang_title"           : "🌍 زمانی خۆت هەڵبژێرە:",
    "lang_saved"           : "✅ زمانەکە گۆڕدرا!",
    "bot_lang_title"       : "🌍 زمانی سەرەکی بۆتەکە هەڵبژێرە:",
    "bot_lang_saved"       : "✅ زمانی سەرەکی بۆتەکە گۆڕدرا بۆ: {lang}",
    "bot_lang_current"     : "زمانی ئێستا: {cur}",
    "force_join"           : "🔒 جۆینی ناچاری\nتکایە سەرەتا ئەم چەناڵانە جۆین بکە، پاشان کلیک لە '✅ جۆینم کرد' بکە:",
    "processing"           : "🔍 دەگەڕێم بۆ لینکەکە...\nچەند چرکەیەک چاوەڕێبە ⏳",
    "found"                : "✅ <b>ڤیدیۆکەت ئامادەیە!</b>\n\n📐 بەرز: {width}x{height}\n\n<i>دابەزاندرا بە بۆتی ئینستاگرام 📥</i>",
    "blocked_msg"          : "⛔ تۆ بلۆک کراویت.",
    "maintenance_msg"      : "🛠 چاکسازی کاتی!\n\n⚙️ بۆتەکەمان لە ژێر نوێکردنەوەیەکی گەورەدایە.\n⏳ زووترین کاتێکدا دەگەڕێینەوە!\n\n📩 پەیوەندی: {dev}",
    "invalid_link"         : "❌ لینکەکە هەڵەیە یان ڤیدیۆکە گشتی نییە!\n\nدڵنیابە لینکەکە:\n• instagram.com/reel/...\n• instagram.com/p/...",
    "dl_fail"              : "❌ هەڵەیەک ڕوویدا! ناتوانرێت دابەزێنرێت.\nتکایە دووبارە هەوڵبدەرەوە.",
    "no_video"             : "❌ ڤیدیۆکە نەدۆزرایەوە! ئەم پۆستە ڤیدیۆی تێدا نییە.",
    "private_post"         : "🔒 ئەم پۆستە تایبەتییە!\nتەنیا پۆستی گشتی دادەگیرێت.",
    "invalid_id"           : "❌ ئایدیەکە دروست نییە! تەنیا ژمارە بنووسە.",
    "user_not_found"       : "⚠️ بەکارهێنەر نەدۆزرایەوە.",
    "broadcast_done"       : "📢 برۆدکاست تەواو بوو\n✅ گەیشت بە: {ok}\n❌ نەگەیشت: {fail}",
    "broadcast_sending"    : "📢 ئەرسال دەکرێت... ({done}/{total})",
    "broadcast_progress"   : "📢 بەردەوامە... ({done}/{total})",
    "welcome_set"          : "✅ نامەی بەخێرهاتن گۆڕدرا.",
    "write_welcome"        : "✍️ نامەی بەخێرهاتن بنووسە:\n(دەتوانیت {name} و {badge} بەکاربێنیت)",
    "write_id"             : "✍️ ئایدی کەسەکە بنووسە:",
    "write_ch"             : "✍️ یوزەرنەیمی چەناڵ بنووسە (نمونە: @mychannel):",
    "vip_yes"              : "بەڵێ 💎",
    "vip_no"               : "نەخێر",
    "badge_owner"          : "👑",
    "badge_super"          : "🌌",
    "badge_admin"          : "🛡",
    "badge_vip"            : "💎",
    "new_user_notify"      : "👤 بەکارهێنەری نوێ!\n\n👤 ناو: {name}\n🔗 یوزەرنەیم: {uname}\n🆔 ئایدی: <code>{uid}</code>\n🌍 زمانی ئەپ: {app_lang}\n📅 کات: {date}",
    "b_notify_block"       : "🚫 بلۆک",
    "b_notify_vip"         : "💎 VIP بکە",
    "b_notify_admin"       : "🛡 ئەدمین بکە",
    "b_notify_info"        : "👤 زانیاری",
    "act_blocked"          : "✅ بلۆک کرا: {id}",
    "act_unblocked"        : "✅ بلۆک لادرا: {id}",
    "act_vip_added"        : "✅ VIP کرا: {id}",
    "act_vip_removed"      : "✅ VIP لادرا: {id}",
    "act_adm_added"        : "✅ ئەدمین کرا: {id}",
    "act_adm_removed"      : "✅ ئەدمین لادرا: {id}",
    "act_sup_added"        : "✅ سوپەر ئەدمین کرا: {id}",
    "act_sup_removed"      : "✅ سوپەر ئەدمین لادرا: {id}",
    "act_ch_wrong_fmt"     : "❌ فۆرماتی چەناڵ هەڵەیە! نمونە: @mychannel",
    "sup_ch_added"         : "✅ چەناڵ زیادکرا: {ch}",
    "userinfo_text"        : "👤 زانیاری بەکارهێنەر\n\n👤 ناو: {name}\n🔗 یوزەرنەیم: @{user}\n🆔 ئایدی: {id}\n💎 VIP: {vip}\n🌍 زمان: {lang}\n📥 دابەزاندن: {dl} جار\n📅 تۆماربوون: {date}",
    "b_dl"                 : "📥 دابەزاندنی نوێ",
    "b_profile"            : "👤 پرۆفایلی من",
    "b_vip"                : "💎 بەشی VIP",
    "b_settings"           : "⚙️ ڕێکخستن و زمان",
    "b_help"               : "ℹ️ فێرکاری",
    "b_channel"            : "📢 کەناڵی بۆت",
    "b_panel"              : "⚙️ پانێڵی کۆنتڕۆڵ",
    "b_back"               : "🔙 گەڕانەوە",
    "b_ku"                 : "🔴🔆🟢 کوردی",
    "b_en"                 : "🇺🇸 English",
    "b_ar"                 : "🇸🇦 العربية",
    "b_cancel"             : "❌ هەڵوەشاندنەوە",
    "b_joined"             : "✅ جۆینم کرد",
    "b_confirm_remove"     : "✅ بەڵێ، بیسڕەوە",
    "b_cancel_remove"      : "❌ نەخێر، هەڵوەشانەوە",
    "b_add"                : "➕ زیادکردن",
    "b_remove"             : "➖ سڕینەوە",
    "b_add_vip"            : "➕ VIP زیادکە",
    "b_rm_vip"             : "➖ VIP لابە",
    "b_refresh"            : "🔄 نوێکردنەوە",
    "b_clear"              : "🗑 سڕینەوە",
    "confirm_remove_admin" : "⚠️ دڵنیایت دەتەوێت ئەم ئەدمینە بسڕیتەوە؟\n🆔 {id}",
    "confirm_remove_super" : "⚠️ دڵنیایت دەتەوێت ئەم سوپەر ئەدمینە بسڕیتەوە؟\n🆔 {id}",
    "confirm_remove_ch"    : "⚠️ دڵنیایت دەتەوێت ئەم چەناڵە بسڕیتەوە؟\n{ch}",
    "unified_panel_title"  : "⚙️ پانێڵی کۆنتڕۆڵ\n\n👥 بەکارهێنەران: {users}\n💎 VIP: {vip}\n🚫 بلۆككراو: {blocked}\n📥 داونلۆد: {dl}\n⏱ Uptime: {uptime}",
    # ── پانێڵ - بەشی ئەدمین ──
    "b_adm_stats"          : "📊 ئامار",
    "b_adm_broadcast"      : "📢 برۆدکاست",
    "b_adm_block"          : "🚫 بلۆک / بەکارهێنەر",
    "b_adm_info"           : "👤 زانیاری بەکارهێنەر",
    "b_adm_admins"         : "🛡 بەڕێوەبردنی ئەدمینەکان",
    "adm_stats_title"      : "📊 ئامارەکان\n\n👥 بەکارهێنەران: {users}\n💎 VIP: {vip}\n🚫 بلۆككراو: {blocked}\n📥 داونلۆد: {dl}\n⏱ Uptime: {uptime}",
    "adm_broadcast_ask"    : "📢 نامەکەت بنووسە بۆ برۆدکاست:\n(هەر جۆرێک — دەق، وێنە، ڤیدیۆ)",
    "adm_block_ask"        : "🚫 ئایدی بەکارهێنەرەکە بنووسە بۆ بلۆک کردن:",
    "adm_info_ask"         : "👤 ئایدی بەکارهێنەرەکە بنووسە:",
    "sup_admins_title"     : "🛡 لیستی ئەدمینەکان ({count} ئەدمین)",
    "sup_add_adm_ask"      : "✍️ ئایدی ئەدمینی نوێ بنووسە:",
    # ── پانێڵ - بەشی سوپەر ──
    "b_sup_vip"            : "💎 بەڕێوەبردنی VIP",
    "b_sup_channels"       : "📢 بەڕێوەبردنی چەناڵەکان",
    "b_sup_maint"          : "🛠 چاکسازی: {status}",
    "b_sup_api"            : "🔌 ڕێکخستنی API",
    "b_sup_botlang"        : "🌍 زمانی سەرەکی بۆت",
    "sup_maint_on"         : "چالاکە ✅",
    "sup_maint_off"        : "ناچالاکە ❌",
    "sup_vip_title"        : "💎 لیستی VIPەکان ({count} کەس)",
    "sup_add_vip_ask"      : "✍️ ئایدی بەکارهێنەرەکە بنووسە بۆ VIP کردن:",
    "sup_ch_title"         : "📢 چەناڵەکان ({count} چەناڵ)",
    "sup_ch_empty"         : "هیچ چەناڵێک نەدۆزرایەوە.",
    "sup_ch_remove_q"      : "کام چەناڵ دەتەوێت بسڕیتەوە؟",
    "sup_add_ch_ask"       : "✍️ یوزەرنەیمی چەناڵ بنووسە (نمونە: @mychannel):",
    "sup_api_title"        : "🔌 هەڵبژاردنی API\n\nئێستا: {act}",
    # ── پانێڵ - بەشی ئۆنەر ──
    "b_own_super"          : "🌌 سوپەر ئەدمینەکان",
    "b_own_welcome"        : "✉️ نامەی بەخێرهاتن",
    "b_own_reset"          : "🔄 ڕێسەتی ئامار",
    "b_own_backup"         : "💾 باکئەپ",
    "own_super_title"      : "🌌 لیستی سوپەر ئەدمینەکان ({count} کەس)",
    "own_add_sup_ask"      : "✍️ ئایدی سوپەر ئەدمینی نوێ بنووسە:",
    "own_reset_done"       : "✅ ئامارەکان ڕێسەت کران.",
    "own_backup_prep"      : "💾 باکئەپ ئامادە دەکرێت...",
    },

# ─────────────────────────────────── ENGLISH ──────────────────────────────────
"en": {
    "welcome"              : "👋 Hello {name} {badge}\n\n📸 Welcome to Instagram Downloader Bot!\n🎬 Download videos and Reels without watermark.\n\n━━━━━━━━━━━━━━━━━━━\n👇 Send me an Instagram link:",
    "help"                 : "📚 How to Use\n\n1️⃣ Copy an Instagram video or Reel link.\n2️⃣ Paste it here.\n3️⃣ Get your video!\n\n✅ Supported:\n• instagram.com/reel/...\n• instagram.com/p/...\n\n💎 VIP: No forced join, faster downloads.\n📩 Contact: {dev}",
    "profile"              : "👤 Profile Card\n\n🆔 ID: {id}\n👤 Name: {name}\n🔗 Username: @{user}\n📅 Joined: {date}\n💎 VIP: {vip}\n🌍 Language: {ulang}\n📥 Downloads: {dl}",
    "vip_info"             : "💎 VIP Benefits\n\n✅ Skip forced channel joins.\n✅ Faster download speed.\n\nBuy VIP: {dev}",
    "lang_title"           : "🌍 Choose your language:",
    "lang_saved"           : "✅ Language changed!",
    "bot_lang_title"       : "🌍 Choose the bot's default language:",
    "bot_lang_saved"       : "✅ Bot default language changed to: {lang}",
    "bot_lang_current"     : "Current language: {cur}",
    "force_join"           : "🔒 Forced Join\nPlease join these channels first, then click '✅ Joined':",
    "processing"           : "🔍 Looking up the link...\nPlease wait ⏳",
    "found"                : "✅ <b>Your video is ready!</b>\n\n📐 Resolution: {width}x{height}\n\n<i>Downloaded via Instagram Bot 📥</i>",
    "blocked_msg"          : "⛔ You are blocked.",
    "maintenance_msg"      : "🛠 Maintenance!\n\n⚙️ The bot is under a major update.\n⏳ We'll be back shortly!\n\n📩 Contact: {dev}",
    "invalid_link"         : "❌ Invalid link or the video is not public!\n\nMake sure the link is:\n• instagram.com/reel/...\n• instagram.com/p/...",
    "dl_fail"              : "❌ An error occurred! Could not download.\nPlease try again.",
    "no_video"             : "❌ Video not found! This post has no video.",
    "private_post"         : "🔒 This post is private!\nOnly public posts can be downloaded.",
    "invalid_id"           : "❌ Invalid ID! Numbers only.",
    "user_not_found"       : "⚠️ User not found.",
    "broadcast_done"       : "📢 Broadcast complete\n✅ Reached: {ok}\n❌ Failed: {fail}",
    "broadcast_sending"    : "📢 Sending... ({done}/{total})",
    "broadcast_progress"   : "📢 In progress... ({done}/{total})",
    "welcome_set"          : "✅ Welcome message updated.",
    "write_welcome"        : "✍️ Write the welcome message:\n(You can use {name} and {badge})",
    "write_id"             : "✍️ Send the user ID:",
    "write_ch"             : "✍️ Send channel username (e.g. @mychannel):",
    "vip_yes"              : "Yes 💎",
    "vip_no"               : "No",
    "badge_owner"          : "👑",
    "badge_super"          : "🌌",
    "badge_admin"          : "🛡",
    "badge_vip"            : "💎",
    "new_user_notify"      : "👤 New User!\n\n👤 Name: {name}\n🔗 Username: {uname}\n🆔 ID: <code>{uid}</code>\n🌍 App lang: {app_lang}\n📅 Date: {date}",
    "b_notify_block"       : "🚫 Block",
    "b_notify_vip"         : "💎 Make VIP",
    "b_notify_admin"       : "🛡 Make Admin",
    "b_notify_info"        : "👤 Info",
    "act_blocked"          : "✅ Blocked: {id}",
    "act_unblocked"        : "✅ Unblocked: {id}",
    "act_vip_added"        : "✅ VIP added: {id}",
    "act_vip_removed"      : "✅ VIP removed: {id}",
    "act_adm_added"        : "✅ Admin added: {id}",
    "act_adm_removed"      : "✅ Admin removed: {id}",
    "act_sup_added"        : "✅ Super admin added: {id}",
    "act_sup_removed"      : "✅ Super admin removed: {id}",
    "act_ch_wrong_fmt"     : "❌ Wrong channel format! Example: @mychannel",
    "sup_ch_added"         : "✅ Channel added: {ch}",
    "userinfo_text"        : "👤 User Info\n\n👤 Name: {name}\n🔗 Username: @{user}\n🆔 ID: {id}\n💎 VIP: {vip}\n🌍 Language: {lang}\n📥 Downloads: {dl}\n📅 Joined: {date}",
    "b_dl"                 : "📥 New Download",
    "b_profile"            : "👤 My Profile",
    "b_vip"                : "💎 VIP Section",
    "b_settings"           : "⚙️ Settings & Language",
    "b_help"               : "ℹ️ Help",
    "b_channel"            : "📢 Bot Channel",
    "b_panel"              : "⚙️ Control Panel",
    "b_back"               : "🔙 Back",
    "b_ku"                 : "🔴🔆🟢 Kurdish",
    "b_en"                 : "🇺🇸 English",
    "b_ar"                 : "🇸🇦 Arabic",
    "b_cancel"             : "❌ Cancel",
    "b_joined"             : "✅ I Joined",
    "b_confirm_remove"     : "✅ Yes, Remove",
    "b_cancel_remove"      : "❌ No, Cancel",
    "b_add"                : "➕ Add",
    "b_remove"             : "➖ Remove",
    "b_add_vip"            : "➕ Add VIP",
    "b_rm_vip"             : "➖ Remove VIP",
    "b_refresh"            : "🔄 Refresh",
    "b_clear"              : "🗑 Clear",
    "confirm_remove_admin" : "⚠️ Are you sure you want to remove this admin?\n🆔 {id}",
    "confirm_remove_super" : "⚠️ Are you sure you want to remove this super admin?\n🆔 {id}",
    "confirm_remove_ch"    : "⚠️ Are you sure you want to remove this channel?\n{ch}",
    "unified_panel_title"  : "⚙️ Control Panel\n\n👥 Users: {users}\n💎 VIP: {vip}\n🚫 Blocked: {blocked}\n📥 Downloads: {dl}\n⏱ Uptime: {uptime}",
    # ── Panel - Admin section ──
    "b_adm_stats"          : "📊 Statistics",
    "b_adm_broadcast"      : "📢 Broadcast",
    "b_adm_block"          : "🚫 Block / User",
    "b_adm_info"           : "👤 User Info",
    "b_adm_admins"         : "🛡 Manage Admins",
    "adm_stats_title"      : "📊 Statistics\n\n👥 Users: {users}\n💎 VIP: {vip}\n🚫 Blocked: {blocked}\n📥 Downloads: {dl}\n⏱ Uptime: {uptime}",
    "adm_broadcast_ask"    : "📢 Write your broadcast message:\n(Any type — text, photo, video)",
    "adm_block_ask"        : "🚫 Send the user ID to block:",
    "adm_info_ask"         : "👤 Send the user ID:",
    "sup_admins_title"     : "🛡 Admin List ({count} admins)",
    "sup_add_adm_ask"      : "✍️ Send the new admin's ID:",
    # ── Panel - Super section ──
    "b_sup_vip"            : "💎 Manage VIP",
    "b_sup_channels"       : "📢 Manage Channels",
    "b_sup_maint"          : "🛠 Maintenance: {status}",
    "b_sup_api"            : "🔌 API Settings",
    "b_sup_botlang"        : "🌍 Bot Default Language",
    "sup_maint_on"         : "Active ✅",
    "sup_maint_off"        : "Inactive ❌",
    "sup_vip_title"        : "💎 VIP List ({count} users)",
    "sup_add_vip_ask"      : "✍️ Send the user ID to make VIP:",
    "sup_ch_title"         : "📢 Channels ({count} channels)",
    "sup_ch_empty"         : "No channels found.",
    "sup_ch_remove_q"      : "Which channel do you want to remove?",
    "sup_add_ch_ask"       : "✍️ Send channel username (e.g. @mychannel):",
    "sup_api_title"        : "🔌 API Selection\n\nCurrent: {act}",
    # ── Panel - Owner section ──
    "b_own_super"          : "🌌 Super Admins",
    "b_own_welcome"        : "✉️ Welcome Message",
    "b_own_reset"          : "🔄 Reset Stats",
    "b_own_backup"         : "💾 Backup",
    "own_super_title"      : "🌌 Super Admin List ({count} users)",
    "own_add_sup_ask"      : "✍️ Send the new super admin's ID:",
    "own_reset_done"       : "✅ Statistics reset successfully.",
    "own_backup_prep"      : "💾 Preparing backup...",
    },

# ─────────────────────────────────── ARABIC ───────────────────────────────────
"ar": {
    "welcome"              : "👋 مرحباً {name} {badge}\n\n📸 أهلاً بك في بوت تنزيل انستغرام!\n🎬 حمّل الفيديوهات والريلز بدون علامة مائية.\n\n━━━━━━━━━━━━━━━━━━━\n👇 أرسل لي رابط انستغرام:",
    "help"                 : "📚 كيفية الاستخدام\n\n1️⃣ انسخ رابط الفيديو أو الريل من انستغرام.\n2️⃣ الصق الرابط هنا.\n3️⃣ احصل على الفيديو!\n\n✅ الروابط المدعومة:\n• instagram.com/reel/...\n• instagram.com/p/...\n\n💎 VIP: بدون اشتراك إجباري، سرعة أعلى.\n📩 للتواصل: {dev}",
    "profile"              : "👤 بطاقة الملف الشخصي\n\n🆔 المعرف: {id}\n👤 الاسم: {name}\n🔗 اسم المستخدم: @{user}\n📅 تاريخ التسجيل: {date}\n💎 VIP: {vip}\n🌍 اللغة: {ulang}\n📥 التنزيلات: {dl}",
    "vip_info"             : "💎 مميزات VIP\n\n✅ تخطي الاشتراك الإجباري.\n✅ سرعة تنزيل أعلى.\n\nلشراء VIP: {dev}",
    "lang_title"           : "🌍 اختر لغتك:",
    "lang_saved"           : "✅ تم تغيير اللغة!",
    "bot_lang_title"       : "🌍 اختر اللغة الافتراضية للبوت:",
    "bot_lang_saved"       : "✅ تم تغيير اللغة الافتراضية إلى: {lang}",
    "bot_lang_current"     : "اللغة الحالية: {cur}",
    "force_join"           : "🔒 الاشتراك الإجباري\nيرجى الانضمام إلى هذه القنوات أولاً، ثم اضغط '✅ انضممت':",
    "processing"           : "🔍 جاري البحث عن الرابط...\nانتظر لحظة ⏳",
    "found"                : "✅ <b>الفيديو جاهز!</b>\n\n📐 الدقة: {width}x{height}\n\n<i>تم التنزيل عبر بوت انستغرام 📥</i>",
    "blocked_msg"          : "⛔ أنت محظور.",
    "maintenance_msg"      : "🛠 صيانة!\n\n⚙️ البوت تحت تحديث كبير.\n⏳ سنعود قريباً!\n\n📩 للتواصل: {dev}",
    "invalid_link"         : "❌ الرابط غير صحيح أو الفيديو غير عام!\n\nتأكد من أن الرابط:\n• instagram.com/reel/...\n• instagram.com/p/...",
    "dl_fail"              : "❌ حدث خطأ! تعذر التنزيل.\nيرجى المحاولة مجدداً.",
    "no_video"             : "❌ لم يتم العثور على فيديو! هذا المنشور لا يحتوي على فيديو.",
    "private_post"         : "🔒 هذا المنشور خاص!\nلا يمكن تنزيل سوى المنشورات العامة.",
    "invalid_id"           : "❌ معرف غير صحيح! أرقام فقط.",
    "user_not_found"       : "⚠️ المستخدم غير موجود.",
    "broadcast_done"       : "📢 اكتمل الإرسال\n✅ تم الإرسال: {ok}\n❌ فشل: {fail}",
    "broadcast_sending"    : "📢 جاري الإرسال... ({done}/{total})",
    "broadcast_progress"   : "📢 جاري... ({done}/{total})",
    "welcome_set"          : "✅ تم تحديث رسالة الترحيب.",
    "write_welcome"        : "✍️ اكتب رسالة الترحيب:\n(يمكنك استخدام {name} و {badge})",
    "write_id"             : "✍️ أرسل معرف المستخدم:",
    "write_ch"             : "✍️ أرسل اسم القناة (مثال: @mychannel):",
    "vip_yes"              : "نعم 💎",
    "vip_no"               : "لا",
    "badge_owner"          : "👑",
    "badge_super"          : "🌌",
    "badge_admin"          : "🛡",
    "badge_vip"            : "💎",
    "new_user_notify"      : "👤 مستخدم جديد!\n\n👤 الاسم: {name}\n🔗 المعرف: {uname}\n🆔 ID: <code>{uid}</code>\n🌍 لغة التطبيق: {app_lang}\n📅 التاريخ: {date}",
    "b_notify_block"       : "🚫 حظر",
    "b_notify_vip"         : "💎 VIP",
    "b_notify_admin"       : "🛡 مشرف",
    "b_notify_info"        : "👤 معلومات",
    "act_blocked"          : "✅ تم الحظر: {id}",
    "act_unblocked"        : "✅ تم رفع الحظر: {id}",
    "act_vip_added"        : "✅ تم إضافة VIP: {id}",
    "act_vip_removed"      : "✅ تم إزالة VIP: {id}",
    "act_adm_added"        : "✅ تم إضافة مشرف: {id}",
    "act_adm_removed"      : "✅ تم إزالة المشرف: {id}",
    "act_sup_added"        : "✅ تم إضافة سوبر مشرف: {id}",
    "act_sup_removed"      : "✅ تم إزالة السوبر مشرف: {id}",
    "act_ch_wrong_fmt"     : "❌ صيغة القناة خاطئة! مثال: @mychannel",
    "sup_ch_added"         : "✅ تمت إضافة القناة: {ch}",
    "userinfo_text"        : "👤 معلومات المستخدم\n\n👤 الاسم: {name}\n🔗 المعرف: @{user}\n🆔 ID: {id}\n💎 VIP: {vip}\n🌍 اللغة: {lang}\n📥 تنزيلات: {dl}\n📅 تاريخ الانضمام: {date}",
    "b_dl"                 : "📥 تنزيل جديد",
    "b_profile"            : "👤 ملفي الشخصي",
    "b_vip"                : "💎 قسم VIP",
    "b_settings"           : "⚙️ الإعدادات واللغة",
    "b_help"               : "ℹ️ مساعدة",
    "b_channel"            : "📢 قناة البوت",
    "b_panel"              : "⚙️ لوحة التحكم",
    "b_back"               : "🔙 رجوع",
    "b_ku"                 : "🔴🔆🟢 كردي",
    "b_en"                 : "🇺🇸 English",
    "b_ar"                 : "🇸🇦 العربية",
    "b_cancel"             : "❌ إلغاء",
    "b_joined"             : "✅ انضممت",
    "b_confirm_remove"     : "✅ نعم، احذف",
    "b_cancel_remove"      : "❌ لا، إلغاء",
    "b_add"                : "➕ إضافة",
    "b_remove"             : "➖ حذف",
    "b_add_vip"            : "➕ إضافة VIP",
    "b_rm_vip"             : "➖ إزالة VIP",
    "b_refresh"            : "🔄 تحديث",
    "b_clear"              : "🗑 مسح",
    "confirm_remove_admin" : "⚠️ هل تريد حذف هذا المشرف؟\n🆔 {id}",
    "confirm_remove_super" : "⚠️ هل تريد حذف هذا السوبر مشرف؟\n🆔 {id}",
    "confirm_remove_ch"    : "⚠️ هل تريد حذف هذه القناة؟\n{ch}",
    "unified_panel_title"  : "⚙️ لوحة التحكم\n\n👥 المستخدمون: {users}\n💎 VIP: {vip}\n🚫 المحظورون: {blocked}\n📥 التنزيلات: {dl}\n⏱ وقت التشغيل: {uptime}",
    # ── لوحة - قسم المشرف ──
    "b_adm_stats"          : "📊 الإحصائيات",
    "b_adm_broadcast"      : "📢 الإذاعة",
    "b_adm_block"          : "🚫 حظر / مستخدم",
    "b_adm_info"           : "👤 معلومات المستخدم",
    "b_adm_admins"         : "🛡 إدارة المشرفين",
    "adm_stats_title"      : "📊 الإحصائيات\n\n👥 المستخدمون: {users}\n💎 VIP: {vip}\n🚫 المحظورون: {blocked}\n📥 التنزيلات: {dl}\n⏱ وقت التشغيل: {uptime}",
    "adm_broadcast_ask"    : "📢 اكتب رسالة الإذاعة:\n(أي نوع — نص، صورة، فيديو)",
    "adm_block_ask"        : "🚫 أرسل معرف المستخدم للحظر:",
    "adm_info_ask"         : "👤 أرسل معرف المستخدم:",
    "sup_admins_title"     : "🛡 قائمة المشرفين ({count} مشرف)",
    "sup_add_adm_ask"      : "✍️ أرسل معرف المشرف الجديد:",
    # ── لوحة - قسم السوبر ──
    "b_sup_vip"            : "💎 إدارة VIP",
    "b_sup_channels"       : "📢 إدارة القنوات",
    "b_sup_maint"          : "🛠 الصيانة: {status}",
    "b_sup_api"            : "🔌 إعدادات API",
    "b_sup_botlang"        : "🌍 لغة البوت الافتراضية",
    "sup_maint_on"         : "نشط ✅",
    "sup_maint_off"        : "غير نشط ❌",
    "sup_vip_title"        : "💎 قائمة VIP ({count} مستخدم)",
    "sup_add_vip_ask"      : "✍️ أرسل معرف المستخدم لترقيته VIP:",
    "sup_ch_title"         : "📢 القنوات ({count} قناة)",
    "sup_ch_empty"         : "لا توجد قنوات.",
    "sup_ch_remove_q"      : "أي قناة تريد حذفها؟",
    "sup_add_ch_ask"       : "✍️ أرسل اسم القناة (مثال: @mychannel):",
    "sup_api_title"        : "🔌 اختيار API\n\nالحالي: {act}",
    # ── لوحة - قسم المالك ──
    "b_own_super"          : "🌌 السوبر مشرفين",
    "b_own_welcome"        : "✉️ رسالة الترحيب",
    "b_own_reset"          : "🔄 إعادة الإحصائيات",
    "b_own_backup"         : "💾 نسخة احتياطية",
    "own_super_title"      : "🌌 قائمة السوبر مشرفين ({count} مستخدم)",
    "own_add_sup_ask"      : "✍️ أرسل معرف السوبر مشرف الجديد:",
    "own_reset_done"       : "✅ تم إعادة تعيين الإحصائيات.",
    "own_backup_prep"      : "💾 جاري تحضير النسخة الاحتياطية...",
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

def is_owner(uid):    return OWNER_ID and uid == OWNER_ID
def is_super(uid):    return uid in super_admins_set or is_owner(uid)
def is_admin(uid):    return uid in admins_set or is_super(uid)
def is_vip(uid):      return uid in vip_set or is_super(uid)
def is_blocked(uid):  return uid in blocked_set
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
async def all_users_data() -> dict:       return await db_get("users") or {}

async def session_save(uid, data):
    data["_ts"] = int(time.time())
    await db_put(f"sessions/{uid}", data)

async def session_get(uid) -> dict | None:
    d = await db_get(f"sessions/{uid}")
    if d and int(time.time()) - d.get("_ts", 0) <= SESSION_TTL: return d
    return None

async def get_user_lang(uid: int) -> str:
    ud = await db_get(f"users/{uid}/lang")
    if ud and ud in L: return ud
    return CFG.get("default_lang", "ku")

async def get_user_display(uid: int) -> str:
    ud = await db_get(f"users/{uid}")
    if ud:
        name     = ud.get("name", str(uid))
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

        # Method 1: Instagram GraphQL API (rich data)
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
                    dims     = media.get("dimensions", {})
                    owner    = media.get("owner", {}).get("username", "")
                    edges    = media.get("edge_media_to_caption", {}).get("edges", [])
                    title    = edges[0].get("node", {}).get("text", "") if edges else ""
                    views    = media.get("video_view_count") or media.get("play_count") or 0
                    likes    = (media.get("edge_media_preview_like") or {}).get("count") or 0
                    comments = (media.get("edge_media_to_comment") or {}).get("count") or 0
                    audio_url = None
                    clips     = media.get("clips_metadata") or {}
                    orig      = (clips.get("original_sound_info") or {})
                    if orig.get("progressive_download_url"):
                        audio_url = orig["progressive_download_url"]
                    if not audio_url:
                        asset = ((clips.get("music_info") or {}).get("music_asset_info") or {})
                        if asset.get("progressive_download_url"):
                            audio_url = asset["progressive_download_url"]
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

        # Method 2: og:video meta tag scraping (fallback)
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
                    t_m = re.search(r'<meta property="og:title" content="([^"]+)"', r.text)
                    raw_title = html.unescape(t_m.group(1)) if t_m else ""
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
                        "views":     0, "likes": 0, "comments": 0,
                        "width":  w.group(1) if w else "?",
                        "height": h.group(1) if h else "?",
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

    # ══════════════════════════════════════════════════════════════════════════
    # ── UNIFIED PANEL ─────────────────────────────────────────────────────────
    if data == "panel_unified":
        if not is_admin(uid): return
        uids_list = await all_uids()
        kb = []

        # Admin section
        kb.append([
            InlineKeyboardButton(tx(lang, "b_adm_stats"),     callback_data="adm_stats"),
            InlineKeyboardButton(tx(lang, "b_adm_broadcast"), callback_data="adm_broadcast"),
        ])
        kb.append([
            InlineKeyboardButton(tx(lang, "b_adm_block"), callback_data="adm_block"),
            InlineKeyboardButton(tx(lang, "b_adm_info"),  callback_data="adm_userinfo"),
        ])
        kb.append([
            InlineKeyboardButton(tx(lang, "b_adm_admins"), callback_data="adm_manage_admins"),
        ])

        # Super section
        if is_super(uid):
            kb.append([InlineKeyboardButton("─── 🌌 Super ───", callback_data="noop")])
            kb.append([
                InlineKeyboardButton(tx(lang, "b_sup_vip"),      callback_data="sup_vips"),
                InlineKeyboardButton(tx(lang, "b_sup_channels"), callback_data="sup_channels"),
            ])
            maint_status = tx(lang, "sup_maint_on") if CFG["maintenance"] else tx(lang, "sup_maint_off")
            kb.append([
                InlineKeyboardButton(tx(lang, "b_sup_maint", status=maint_status), callback_data="sup_toggle_maint"),
                InlineKeyboardButton(tx(lang, "b_sup_api"),                        callback_data="sup_api_settings"),
            ])
            kb.append([
                InlineKeyboardButton(tx(lang, "b_sup_botlang"), callback_data="sup_bot_lang"),
            ])

        # Owner section
        if is_owner(uid):
            kb.append([InlineKeyboardButton("─── 👑 Owner ───", callback_data="noop")])
            kb.append([
                InlineKeyboardButton(tx(lang, "b_own_super"),   callback_data="own_super_adms"),
                InlineKeyboardButton(tx(lang, "b_own_welcome"), callback_data="own_welcome"),
            ])
            kb.append([
                InlineKeyboardButton(tx(lang, "b_own_reset"),  callback_data="own_reset_stats"),
                InlineKeyboardButton(tx(lang, "b_own_backup"), callback_data="own_backup"),
            ])

        kb += back(lang)
        await q.edit_message_text(
            tx(lang, "unified_panel_title",
               users=len(uids_list), vip=len(vip_set),
               blocked=len(blocked_set), dl=fmt(CFG.get("total_dl", 0)),
               uptime=uptime()),
            reply_markup=InlineKeyboardMarkup(kb)
        ); return

    if data == "noop":
        return

    # ══════════════════════════════════════════════════════════════════════════
    # ── ADMIN SECTION ─────────────────────────────────────────────────────────
    if data.startswith("adm_"):
        if not is_admin(uid): return

        if data == "adm_stats":
            txt = tx(lang, "adm_stats_title",
                users=len(await all_uids()), vip=len(vip_set),
                blocked=len(blocked_set), dl=fmt(CFG.get("total_dl", 0)), uptime=uptime()
            )
            await q.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(tx(lang, "b_refresh"), callback_data="adm_stats")],
                 *back(lang, "panel_unified")]
            )); return

        if data == "adm_broadcast":
            waiting_state[uid] = "broadcast_all"
            await q.edit_message_text(
                tx(lang, "adm_broadcast_ask"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx(lang, "b_cancel"), callback_data="panel_unified")]])
            ); return

        if data == "adm_block":
            waiting_state[uid] = "action_blk_add"
            await q.edit_message_text(
                tx(lang, "adm_block_ask"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx(lang, "b_cancel"), callback_data="panel_unified")]])
            ); return

        if data == "adm_userinfo":
            waiting_state[uid] = "action_info_check"
            await q.edit_message_text(
                tx(lang, "adm_info_ask"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx(lang, "b_cancel"), callback_data="panel_unified")]])
            ); return

        if data == "adm_manage_admins":
            adm_list = admins_set - {OWNER_ID}
            lines = []
            for aid in adm_list:
                display = await get_user_display(aid)
                lines.append(display)
            text = tx(lang, "sup_admins_title", count=len(adm_list))
            if lines:
                text += "\n" + "\n".join(f"• {l}" for l in lines)
            kb = [
                [InlineKeyboardButton(tx(lang, "b_add"), callback_data="sup_add_adm")],
            ]
            if is_super(uid):
                kb[0].append(InlineKeyboardButton(tx(lang, "b_remove"), callback_data="sup_rm_adm_list"))
            kb += back(lang, "panel_unified")
            await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb)); return

    # ══════════════════════════════════════════════════════════════════════════
    # ── SUPER SECTION ─────────────────────────────────────────────────────────
    if data.startswith("sup_"):
        if not is_super(uid): return

        if data == "sup_toggle_maint":
            CFG["maintenance"] = not CFG["maintenance"]; await save_cfg()
            q.data = "panel_unified"; await on_callback(update, ctx); return

        if data == "sup_bot_lang":
            cur = LANG_NAMES.get(CFG.get("default_lang", "ku"), "?")
            kb  = bot_lang_select_buttons() + back(lang, "panel_unified")
            await q.edit_message_text(
                tx(lang, "bot_lang_title") + "\n\n" + tx(lang, "bot_lang_current", cur=cur),
                reply_markup=InlineKeyboardMarkup(kb)
            ); return

        if data == "sup_api_settings":
            act = CFG.get("active_api", "auto")
            act_name = {"auto": "Auto", "tikwm": "TikWM", "hyper": "Hyper API"}.get(act, act)
            kb = [
                [InlineKeyboardButton(f"{'✅ ' if act=='auto'  else ''}Auto",      callback_data="sup_setapi_auto")],
                [InlineKeyboardButton(f"{'✅ ' if act=='tikwm' else ''}TikWM",     callback_data="sup_setapi_tikwm")],
                [InlineKeyboardButton(f"{'✅ ' if act=='hyper' else ''}Hyper API", callback_data="sup_setapi_hyper")],
                *back(lang, "panel_unified"),
            ]
            await q.edit_message_text(tx(lang, "sup_api_title", act=act_name), reply_markup=InlineKeyboardMarkup(kb)); return

        if data.startswith("sup_setapi_"):
            CFG["active_api"] = data.split("_")[2]; await save_cfg()
            q.data = "sup_api_settings"; await on_callback(update, ctx); return

        if data == "sup_add_adm":
            waiting_state[uid] = "action_adm_add"
            await q.edit_message_text(
                tx(lang, "sup_add_adm_ask"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx(lang, "b_cancel"), callback_data="adm_manage_admins")]])
            ); return

        if data == "sup_rm_adm_list":
            adm_list = admins_set - super_admins_set - {OWNER_ID}
            if not adm_list:
                await q.answer("—", show_alert=True); return
            kb = []
            for aid in adm_list:
                display = await get_user_display(aid)
                kb.append([InlineKeyboardButton(f"❌ {display}", callback_data=f"sup_confirm_rm_adm_{aid}")])
            kb += back(lang, "adm_manage_admins")
            await q.edit_message_text(tx(lang, "sup_admins_title", count=len(adm_list)), reply_markup=InlineKeyboardMarkup(kb)); return

        if data.startswith("sup_confirm_rm_adm_"):
            tid = int(data.split("_")[4])
            await q.edit_message_text(
                tx(lang, "confirm_remove_admin", id=tid),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(tx(lang, "b_confirm_remove"), callback_data=f"sup_do_rm_adm_{tid}")],
                    [InlineKeyboardButton(tx(lang, "b_cancel_remove"),  callback_data="adm_manage_admins")],
                ])
            ); return

        if data.startswith("sup_do_rm_adm_"):
            tid = int(data.split("_")[4])
            admins_set.discard(tid); await save_cfg()
            await q.answer(tx(lang, "act_adm_removed", id=tid), show_alert=True)
            q.data = "adm_manage_admins"; await on_callback(update, ctx); return

        if data == "sup_vips":
            vip_real = vip_set - super_admins_set - {OWNER_ID}
            lines = []
            for vid in vip_real:
                display = await get_user_display(vid)
                lines.append(display)
            text = tx(lang, "sup_vip_title", count=len(vip_real))
            if lines:
                text += "\n" + "\n".join(f"• {l}" for l in lines)
            kb = [
                [InlineKeyboardButton(tx(lang, "b_add_vip"), callback_data="sup_add_vip"),
                 InlineKeyboardButton(tx(lang, "b_rm_vip"),  callback_data="sup_rm_vip_list")],
                *back(lang, "panel_unified"),
            ]
            await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb)); return

        if data == "sup_add_vip":
            waiting_state[uid] = "action_vip_add"
            await q.edit_message_text(
                tx(lang, "sup_add_vip_ask"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx(lang, "b_cancel"), callback_data="sup_vips")]])
            ); return

        if data == "sup_rm_vip_list":
            vip_real = vip_set - super_admins_set - {OWNER_ID}
            if not vip_real:
                await q.answer(tx(lang, "sup_ch_empty"), show_alert=True); return
            kb = []
            for vid in vip_real:
                display = await get_user_display(vid)
                kb.append([InlineKeyboardButton(f"❌ {display}", callback_data=f"sup_confirm_rm_vip_{vid}")])
            kb += back(lang, "sup_vips")
            await q.edit_message_text(tx(lang, "sup_vip_title", count=len(vip_real)), reply_markup=InlineKeyboardMarkup(kb)); return

        if data.startswith("sup_confirm_rm_vip_"):
            vid = int(data.split("_")[4])
            await q.edit_message_text(
                tx(lang, "confirm_remove_admin", id=vid),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(tx(lang, "b_confirm_remove"), callback_data=f"sup_do_rm_vip_{vid}")],
                    [InlineKeyboardButton(tx(lang, "b_cancel_remove"),  callback_data="sup_vips")],
                ])
            ); return

        if data.startswith("sup_do_rm_vip_"):
            vid = int(data.split("_")[4])
            vip_set.discard(vid); await user_field(vid, "vip", False); await save_cfg()
            await q.answer(tx(lang, "act_vip_removed", id=vid), show_alert=True)
            q.data = "sup_vips"; await on_callback(update, ctx); return

        if data == "sup_channels":
            lst_lines = [f"• {ch}" for ch in channels_list]
            text = tx(lang, "sup_ch_title", count=len(channels_list))
            if lst_lines:
                text += "\n" + "\n".join(lst_lines)
            else:
                text += f"\n{tx(lang, 'sup_ch_empty')}"
            kb = [
                [InlineKeyboardButton(tx(lang, "b_add"),    callback_data="sup_add_ch"),
                 InlineKeyboardButton(tx(lang, "b_remove"), callback_data="sup_rm_ch_list")],
                *back(lang, "panel_unified"),
            ]
            await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb)); return

        if data == "sup_add_ch":
            waiting_state[uid] = "action_add_ch"
            await q.edit_message_text(
                tx(lang, "sup_add_ch_ask"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx(lang, "b_cancel"), callback_data="sup_channels")]])
            ); return

        if data == "sup_rm_ch_list":
            if not channels_list: await q.answer(tx(lang, "sup_ch_empty"), show_alert=True); return
            kb = [[InlineKeyboardButton(f"❌ {c}", callback_data=f"sup_confirm_rm_ch_{c}")] for c in channels_list]
            kb += back(lang, "sup_channels")
            await q.edit_message_text(tx(lang, "sup_ch_remove_q"), reply_markup=InlineKeyboardMarkup(kb)); return

        if data.startswith("sup_confirm_rm_ch_"):
            ch = data[len("sup_confirm_rm_ch_"):]
            await q.edit_message_text(
                tx(lang, "confirm_remove_ch", ch=ch),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(tx(lang, "b_confirm_remove"), callback_data=f"sup_do_rm_ch_{ch}")],
                    [InlineKeyboardButton(tx(lang, "b_cancel_remove"),  callback_data="sup_channels")],
                ])
            ); return

        if data.startswith("sup_do_rm_ch_"):
            ch = data[len("sup_do_rm_ch_"):]
            if ch in channels_list: channels_list.remove(ch); await save_cfg()
            q.data = "sup_channels"; await on_callback(update, ctx); return

    # ══════════════════════════════════════════════════════════════════════════
    # ── OWNER SECTION ─────────────────────────────────────────────────────────
    if data.startswith("own_"):
        if not is_owner(uid): return

        if data == "own_super_adms":
            sup_real = super_admins_set - {OWNER_ID}
            lines = []
            for sid in sup_real:
                display = await get_user_display(sid)
                lines.append(display)
            text = tx(lang, "own_super_title", count=len(sup_real))
            if lines:
                text += "\n" + "\n".join(f"• {l}" for l in lines)
            kb = [
                [InlineKeyboardButton(tx(lang, "b_add"),    callback_data="own_add_sup"),
                 InlineKeyboardButton(tx(lang, "b_remove"), callback_data="own_rm_sup_list")],
                *back(lang, "panel_unified"),
            ]
            await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb)); return

        if data == "own_add_sup":
            waiting_state[uid] = "action_sup_add"
            await q.edit_message_text(
                tx(lang, "own_add_sup_ask"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx(lang, "b_cancel"), callback_data="own_super_adms")]])
            ); return

        if data == "own_rm_sup_list":
            sup_real = super_admins_set - {OWNER_ID}
            if not sup_real:
                await q.answer("—", show_alert=True); return
            kb = []
            for sid in sup_real:
                display = await get_user_display(sid)
                kb.append([InlineKeyboardButton(f"❌ {display}", callback_data=f"own_confirm_rm_sup_{sid}")])
            kb += back(lang, "own_super_adms")
            await q.edit_message_text(tx(lang, "own_super_title", count=len(sup_real)), reply_markup=InlineKeyboardMarkup(kb)); return

        if data.startswith("own_confirm_rm_sup_"):
            sid = int(data.split("_")[4])
            await q.edit_message_text(
                tx(lang, "confirm_remove_super", id=sid),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(tx(lang, "b_confirm_remove"), callback_data=f"own_do_rm_sup_{sid}")],
                    [InlineKeyboardButton(tx(lang, "b_cancel_remove"),  callback_data="own_super_adms")],
                ])
            ); return

        if data.startswith("own_do_rm_sup_"):
            sid = int(data.split("_")[4])
            super_admins_set.discard(sid); await save_cfg()
            await q.answer(tx(lang, "act_sup_removed", id=sid), show_alert=True)
            q.data = "own_super_adms"; await on_callback(update, ctx); return

        if data == "own_welcome":
            waiting_state[uid] = "set_welcome"
            await q.edit_message_text(
                tx(lang, "write_welcome"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(tx(lang, "b_clear"), callback_data="own_clear_welcome")],
                    *back(lang, "panel_unified"),
                ])
            ); return

        if data == "own_clear_welcome":
            CFG["welcome_msg"] = ""; await save_cfg()
            q.data = "panel_unified"; await on_callback(update, ctx); return

        if data == "own_reset_stats":
            for k in ("total_dl", "total_users"): CFG[k] = 0
            await save_cfg(); await q.answer(tx(lang, "own_reset_done"), show_alert=True); return

        if data == "own_backup":
            await q.answer(tx(lang, "own_backup_prep"), show_alert=False)
            bdata = {"time": now_str(), "cfg": CFG, "users": await all_users_data()}
            bio   = io.BytesIO(json.dumps(bdata, ensure_ascii=False, indent=2).encode())
            bio.name = f"Backup_{now_str()}.json"
            try: await ctx.bot.send_document(uid, bio)
            except: pass
            return

# ── Message Handler ────────────────────────────────────────────────────────────
async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    uid  = update.effective_user.id
    msg  = update.message
    txt  = msg.text or ""
    lang = await get_user_lang(uid)

    # ── Waiting State ──────────────────────────────────────────────────────────
    if uid in waiting_state:
        state = waiting_state.pop(uid)

        if state == "set_welcome":
            CFG["welcome_msg"] = txt; await save_cfg()
            await msg.reply_text(tx(lang, "welcome_set")); return

        if state.startswith("broadcast_"):
            all_u = await all_uids(); ok = fail = 0
            st = await msg.reply_text(tx(lang, "broadcast_sending", done=0, total=len(all_u)))
            for i, t in enumerate(all_u):
                try:
                    await ctx.bot.copy_message(chat_id=t, from_chat_id=msg.chat_id, message_id=msg.message_id)
                    ok += 1; await asyncio.sleep(0.04)
                except: fail += 1
                if i % 100 == 0 and i > 0:
                    try: await st.edit_text(tx(lang, "broadcast_progress", done=i, total=len(all_u)))
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
                ulang_str = LANG_NAMES.get(ud.get("lang", "—"), ud.get("lang", "—"))
                vip_str   = tx(lang, "vip_yes") if ud.get("vip") else tx(lang, "vip_no")
                await msg.reply_text(tx(lang, "userinfo_text",
                    name=ud.get("name","—"), user=ud.get("user","—"),
                    id=tid, vip=vip_str, lang=ulang_str,
                    dl=ud.get("dl", 0), date=ud.get("date","—")
                ))
            elif action == "adm_add":
                admins_set.add(tid); await save_cfg()
                await msg.reply_text(tx(lang, "act_adm_added", id=tid))
            elif action == "sup_add":
                super_admins_set.add(tid); admins_set.add(tid); await save_cfg()
                await msg.reply_text(tx(lang, "act_sup_added", id=tid))
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
        "status"   : "running",
        "bot_token": t,
        "firebase" : d,
        "owner_id" : o,
        "uptime"   : uptime(),
    }

@app.get("/api/video")
async def get_video(postUrl: str = ""):
    if not postUrl:
        return {"ok": False, "error": "postUrl parameter is required"}
    data = await fetch_instagram(postUrl)
    if not data:
        return {"ok": False, "error": "Could not fetch video. Post may be private or invalid."}
    return {"ok": True, "data": data}
