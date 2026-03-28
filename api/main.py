# ╔══════════════════════════════════════════════════════════════════════════╗
# ║  ██╗███╗  ██╗███████╗████████╗ █████╗     ██████╗  ██████╗ ████████╗   ║
# ║  ██║████╗ ██║██╔════╝╚══██╔══╝██╔══██╗    ██╔══██╗██╔═══██╗╚══██╔══╝  ║
# ║  ██║██╔██╗██║███████╗   ██║   ███████║    ██████╔╝██║   ██║   ██║     ║
# ║  ██║██║╚████║╚════██║   ██║   ██╔══██║    ██╔══██╗██║   ██║   ██║     ║
# ║  ██║██║ ╚███║███████║   ██║   ██║  ██║    ██████╔╝╚██████╔╝   ██║     ║
# ║  ╚═╝╚═╝  ╚══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝    ╚═════╝  ╚═════╝    ╚═╝     ║
# ╠══════════════════════════════════════════════════════════════════════════╣
# ║  Version  : v4.0 ULTRA PRO MAX                                          ║
# ║  Owner    : @j4ck_721s          Channel : @jack_721_mod                 ║
# ║  Stack    : FastAPI · python-telegram-bot · Firebase · Vercel           ║
# ║  © 2025-2026  All rights reserved — Unauthorized resale is prohibited   ║
# ╚══════════════════════════════════════════════════════════════════════════╝

import os, time, logging, httpx, re, html, asyncio, json, io, traceback
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    InputMediaPhoto, ForceReply
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
    MessageHandler, CallbackQueryHandler, filters,
)
from telegram.constants import ChatMemberStatus
from telegram.error import BadRequest

# ==============================================================================
# ── 1. CONFIGURATION
# ==============================================================================
TOKEN        = os.getenv("BOT_TOKEN") or "DUMMY_TOKEN"
DB_URL       = os.getenv("DB_URL") or ""
DB_SECRET    = os.getenv("DB_SECRET") or ""
OWNER_ID     = int(os.getenv("OWNER_ID") or "0")
DEV          = os.getenv("DEV_USERNAME") or "@j4ck_721s"
CHANNEL_URL  = os.getenv("CHANNEL_URL") or "https://t.me/jack_721_mod"
START_TIME   = time.time()
SESSION_TTL  = 1800

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
    "max_photos"   : 15,
    "api_timeout"  : 60,
    "vip_bypass"   : True,
    "admin_bypass" : True,
    "total_dl"     : 0,
    "total_users"  : 0,
    "active_api"   : "auto",
}

# ==============================================================================
# ── 2. LANGUAGE DICTIONARY
# ==============================================================================
L: dict = {
"ku": {
    "welcome"             : "👋 سڵاو {name} {badge}\n\n📸 بەخێربێیت بۆ پێشکەوتووترین بۆتی ئینستاگرام!\n📥 ڤیدیۆ، وێنە و گۆرانی دابەزێنە بە بەرزترین خێرایی.\n\n━━━━━━━━━━━━━━━━━━━\n👇 تەنیا لینکی ئینستاگرامەکە بنێرەم:",
    "help"                : "📚 ڕێنمایی بەکارهێنان\n\n1️⃣ لینکی ڤیدیۆ لە ئینستاگرام کۆپی بکە.\n2️⃣ لینکەکە لێرە پەیست بکە.\n3️⃣ جۆری دابەزاندن هەڵبژێرە!\n\n🎥 ڤیدیۆ: بەبێ واتەرمارک.\n📸 وێنە: هەموو وێنەکانی پۆستەکە.\n🎵 گۆرانی: فۆرماتی MP3.\n\n💎 VIP: بێ جۆینی ناچاری.\n📩 پەیوەندی: {dev}",
    "profile"             : "👤 کارتی پرۆفایل\n\n🆔 ئایدی: {id}\n👤 ناو: {name}\n🔗 یوزەرنەیم: @{user}\n📅 تۆماربوون: {date}\n💎 VIP: {vip}\n🌍 زمان: {ulang}\n📥 دابەزاندن: {dl} جار",
    "vip_info"            : "💎 تایبەتمەندییەکانی VIP\n\n✅ بەبێ جۆینی ناچاری.\n✅ خێرایی دابەزاندنی زیاتر.\n✅ وێنەی بێسنوور.\n\nبۆ کڕینی VIP: {dev}",
    "lang_title"          : "🌍 زمانی خۆت هەڵبژێرە:",
    "lang_saved"          : "✅ زمانەکە گۆڕدرا!",
    "bot_lang_title"      : "🌍 زمانی سەرەکی بۆتەکە هەڵبژێرە:\n(ئەمە زمانی سەرەکی بۆ هەموو بەکارهێنەرانە)",
    "bot_lang_saved"      : "✅ زمانی سەرەکی بۆتەکە گۆڕدرا بۆ: {lang}",
    "bot_lang_current"    : "🔵 ئێستا: {cur}",
    "force_join"          : "🔒 جۆینی ناچاری\nتکایە سەرەتا ئەم چەناڵانە جۆین بکە، پاشان کلیک لە '✅ جۆینم کرد' بکە:",
    "found"               : "📝 سەردێڕ: {title}\n👤 خاوەن: {owner}\n\n📊 ئامارەکان:\n👁 بینەر: {views}  \n❤️ لایک: {likes}  \n💬 کۆمێنت: {comments}\n\n🎬 <a href=\"https://t.me/Instagram_Downloader_Jack_Robot\">کلیک لێرە بکە — دابەزاندن دەستپێبکە</a>",
    "sending_photos"      : "📸 وێنەکان ئامادە دەکرێن...",
    "blocked_msg"         : "⛔ تۆ بلۆک کراویت.",
    "maintenance_msg"     : "🛠 چاکسازی کاتی!\n\n⚙️ بۆتەکەمان لە ژێر نوێکردنەوەیەکی گەورەدایە.\n⏳ زووترین کاتێکدا دەگەڕێینەوە!\n\n📩 پەیوەندی: {dev}",
    "session_expired"     : "⚠️ کات بەسەرچوو! لینکەکە سەرلەنوێ بنێرەوە.",
    "invalid_link"        : "❌ لینکەکە هەڵەیە یان نادۆزرێتەوە!",
    "dl_fail"             : "❌ هەڵەیەک ڕوویدا! ناتوانرێت دابەزێنرێت.",
    "no_photo"            : "❌ ئەم پۆستە وێنەی تێدا نییە!",
    "no_video"            : "❌ ڤیدیۆکە نەدۆزرایەوە!",
    "no_audio"            : "❌ دەنگەکە بەردەست نییە!",
    "invalid_id"          : "❌ ئایدیەکە دروست نییە! تەنیا ژمارە بنووسە.",
    "user_not_found"      : "⚠️ بەکارهێنەر نەدۆزرایەوە.",
    "broadcast_done"      : "📢 برۆدکاست تەواو بوو\n✅ گەیشت بە: {ok}\n❌ نەگەیشت: {fail}",
    "broadcast_sending"   : "⏳ ناردن دەستی پێکرد بۆ {total} کەس...",
    "broadcast_progress"  : "⏳ ناردن: {done}/{total}...",
    "welcome_set"         : "✅ نامەی بەخێرهاتن گۆڕدرا.",
    "write_welcome"       : "✍️ نامەی بەخێرهاتن بنووسە:\n(دەتوانیت {name} و {badge} بەکاربێنیت)",
    "write_id"            : "✍️ ئایدی کەسەکە بنووسە و بینێرە:",
    "write_ch"            : "✍️ یوزەرنەیمی چەناڵ بنووسە (نمونە: @mychannel):",
    "ask_link_prompt"     : "🔗 تکایە لینکی ئینستاگرامەکە بنێرەم:",
    "vip_yes"             : "بەڵێ 💎",
    "vip_no"              : "نەخێر",
    "badge_owner"         : "👑",
    "badge_super"         : "🌌",
    "badge_admin"         : "🛡",
    "badge_vip"           : "💎",
    "b_dl"                : "📥 دابەزاندنی نوێ",
    "b_profile"           : "👤 پرۆفایلی من",
    "b_vip"               : "💎 بەشی VIP",
    "b_settings"          : "⚙️ ڕێکخستن و زمان",
    "b_help"              : "ℹ️ فێرکاری",
    "b_channel"           : "📢 کەناڵی بۆت",
    "b_panel"             : "⚙️ پانێڵی کۆنتڕۆڵ",
    "b_back"              : "🔙 گەڕانەوە",
    "b_delete"            : "🗑 سڕینەوە",
    "b_joined"            : "✅ جۆینم کرد",
    "b_video"             : "🎥 ڤیدیۆ (بێ واتەرمارک)",
    "b_photos"            : "📸 وێنەکان ({n})",
    "b_audio"             : "🎵 گۆرانی (MP3)",
    "b_ku"                : "🔴🔆🟢 کوردی",
    "b_en"                : "🇺🇸 English",
    "b_ar"                : "🇸🇦 العربية",
    "b_cancel"            : "❌ هەڵوەشاندنەوە",
    "b_confirm_remove"    : "✅ بەڵێ، بیسڕەوە",
    "b_cancel_remove"     : "❌ نەخێر، هەڵوەشانەوە",
    "confirm_remove_admin": "⚠️ دڵنیایت دەتەوێت ئەم ئەدمینە بسڕیتەوە؟\n🆔 {id}",
    "confirm_remove_super": "⚠️ دڵنیایت دەتەوێت ئەم سوپەر ئەدمینە بسڕیتەوە؟\n🆔 {id}",
    "confirm_remove_ch"   : "⚠️ دڵنیایت دەتەوێت ئەم چەناڵە بسڕیتەوە؟\n{ch}",
    "unified_panel_title" : "⚙️ پانێڵی کۆنتڕۆڵ\n\n👥 بەکارهێنەران: {users}\n💎 VIP: {vip}\n🚫 بلۆككراو: {blocked}\n📥 داونلۆد: {dl}\n⏱ Uptime: {uptime}",
    "adm_stats_title"     : "📊 ئامارەکان:\n👥 کۆی بەکارهێنەران: {users}\n💎 VIP: {vip}\n🚫 بلۆككراو: {blocked}\n📥 داونلۆدەکان: {dl}\n⏱ Uptime: {uptime}",
    "adm_broadcast_ask"   : "✍️ پەیامەکەت بنێرە (تێکست، وێنە، ڤیدیۆ):",
    "adm_block_ask"       : "🚫 بلۆككردنی بەکارهێنەر:\n\n{write_id}",
    "adm_info_ask"        : "👤 زانیاری بەکارهێنەر:\n\n{write_id}",
    "b_adm_stats"         : "📊 ئامارەکان",
    "b_adm_broadcast"     : "📢 برۆدکاست",
    "b_adm_block"         : "🚫 بلۆككردن",
    "b_adm_info"          : "👤 زانیاری کەس",
    "b_adm_admins"        : "👮 ئەدمینەکان",
    "sup_panel_title"     : "🌌 بەشی سوپەر",
    "sup_maint_on"        : "🔴 چالاکە",
    "sup_maint_off"       : "🟢 ناچالاکە",
    "sup_admins_title"    : "👮 ئەدمینەکان ({count}):",
    "sup_vip_title"       : "💎 VIP ({count}):",
    "sup_ch_title"        : "📢 چەناڵەکان ({count}):",
    "sup_ch_empty"        : "📭 بەتاڵە",
    "sup_ch_remove_q"     : "کام چەناڵ دەسڕیتەوە؟",
    "sup_ch_added"        : "✅ {ch} زیاد کرا!",
    "sup_add_adm_ask"     : "➕ ئەدمینی نوێ:\n\n{write_id}",
    "sup_rm_adm_ask"      : "➖ لابردنی ئەدمین:\n\n{write_id}",
    "sup_add_vip_ask"     : "💎 پێدانی VIP:\n\n{write_id}",
    "sup_rm_vip_ask"      : "➖ سەندنەوەی VIP:\n\n{write_id}",
    "sup_add_ch_ask"      : "📢 زیادکردنی چەناڵ:\n\n{write_ch}",
    "b_sup_admins"        : "👮 ئەدمینەکان",
    "b_sup_vip"           : "💎 VIP",
    "b_sup_channels"      : "📢 چەناڵەکان",
    "b_sup_maint"         : "🛠 چاکسازی: {status}",
    "b_sup_botlang"       : "🌍 زمانی بۆت",
    "b_add"               : "➕ زیادکردن",
    "b_remove"            : "➖ لابردن",
    "b_add_vip"           : "➕ VIP",
    "b_rm_vip"            : "➖ VIP",
    "b_refresh"           : "🔄 نوێکردنەوە",
    "b_clear"             : "🗑 سڕینەوە",
    "own_panel_title"     : "👑 بەشی خاوەن",
    "own_super_title"     : "🌌 سوپەر ئەدمینەکان ({count}):",
    "own_add_sup_ask"     : "➕ سوپەر ئەدمینی نوێ:\n\n{write_id}",
    "own_rm_sup_ask"      : "➖ لابردنی سوپەر ئەدمین:\n\n{write_id}",
    "b_own_super"         : "🌌 سوپەر ئەدمین",
    "b_own_botlang"       : "🌍 زمانی بۆت",
    "b_own_welcome"       : "📝 نامەی خێرهاتن",
    "b_own_reset"         : "🗑 ڕیسێتی ئامار",
    "b_own_backup"        : "💾 باکئەپ",
    "own_reset_done"      : "✅ ئامارەکان سفر کرانەوە!",
    "own_backup_prep"     : "⏳ ئامادە دەکرێت...",
    "new_user_notify"     : "🔔 بەکارهێنەری نوێ!\n\n👤 ناو: {name}\n🔗 یوزەر: {uname}\n🆔 ئایدی: {uid}\n🌐 زمانی ئەپ: {app_lang}\n📅 {date}",
    "b_notify_block"      : "🚫 بلۆک",
    "b_notify_vip"        : "💎 VIP",
    "b_notify_admin"      : "🛡 ئەدمین",
    "b_notify_info"       : "👤 زانیاری",
    "act_blocked"         : "🚫 {id} بلۆک کرا!",
    "act_unblocked"       : "✅ {id} بلۆکەکەی لابرا.",
    "act_adm_added"       : "✅ {id} بوو بە ئەدمین!",
    "act_adm_removed"     : "➖ {id} لە ئەدمین لابرا.",
    "act_sup_added"       : "🌌 {id} بوو بە سوپەر ئەدمین!",
    "act_sup_removed"     : "➖ {id} لە سوپەر لابرا.",
    "act_vip_added"       : "💎 {id} کرایە VIP!",
    "act_vip_removed"     : "➖ VIP لە {id} سەندرایەوە.",
    "act_ch_wrong_fmt"    : "❌ فۆرماتەکە هەڵەیە! بنووسە: @channelname",
    "userinfo_text"       : "👤 ناو: {name}\n🔗 یوزەر: @{user}\n🆔 ئایدی: {id}\n💎 VIP: {vip}\n🌍 زمان: {lang}\n📥 داونلۆد: {dl}\n📅 تۆماربوون: {date}",
},
"en": {
    "welcome"             : "👋 Hello {name} {badge}\n\n📸 Welcome to the most advanced Instagram Bot!\n📥 Download videos, photos & audio at top speed.\n\n━━━━━━━━━━━━━━━━━━━\n👇 Just send me an Instagram link:",
    "help"                : "📚 How to Use\n\n1️⃣ Copy an Instagram video link.\n2️⃣ Paste it here.\n3️⃣ Choose your download type!\n\n🎥 Video: No watermark.\n📸 Photos: All post images.\n🎵 Audio: MP3 format.\n\n💎 VIP: No forced join.\n📩 Contact: {dev}",
    "profile"             : "👤 Your Profile\n\n🆔 ID: {id}\n👤 Name: {name}\n🔗 Username: @{user}\n📅 Joined: {date}\n💎 VIP: {vip}\n🌍 Language: {ulang}\n📥 Downloads: {dl} times",
    "vip_info"            : "💎 VIP Benefits\n\n✅ Skip forced channel joins.\n✅ Faster download speed.\n✅ Unlimited photos.\n\nBuy VIP: {dev}",
    "lang_title"          : "🌍 Choose your language:",
    "lang_saved"          : "✅ Language changed!",
    "bot_lang_title"      : "🌍 Choose the bot default language:\n(This applies to all users globally)",
    "bot_lang_saved"      : "✅ Bot default language changed to: {lang}",
    "bot_lang_current"    : "🔵 Current: {cur}",
    "force_join"          : "🔒 Forced Join\nPlease join the channels below first, then click '✅ I Joined':",
    "found"               : "📝 Title: {title}\n👤 Author: {owner}\n\n📊 Stats:\n👁 Views: {views}  \n❤️ Likes: {likes}  \n💬 Comments: {comments}\n\n🎬 <a href=\"https://t.me/Instagram_Downloader_Jack_Robot\">Click Here — Start Downloading</a>",
    "sending_photos"      : "📸 Preparing photos...",
    "blocked_msg"         : "⛔ You have been blocked.",
    "maintenance_msg"     : "🛠 Maintenance Mode!\n\n⚙️ The bot is under a major update.\n⏳ We'll be back soon!\n\n📩 Contact: {dev}",
    "session_expired"     : "⚠️ Session expired! Please send the link again.",
    "invalid_link"        : "❌ Invalid link or not found!",
    "dl_fail"             : "❌ An error occurred! Could not download.",
    "no_photo"            : "❌ This post has no photos!",
    "no_video"            : "❌ Video not found!",
    "no_audio"            : "❌ Audio not available!",
    "invalid_id"          : "❌ Invalid ID! Numbers only.",
    "user_not_found"      : "⚠️ User not found.",
    "broadcast_done"      : "📢 Broadcast Complete\n✅ Delivered: {ok}\n❌ Failed: {fail}",
    "broadcast_sending"   : "⏳ Sending to {total} users...",
    "broadcast_progress"  : "⏳ Sending: {done}/{total}...",
    "welcome_set"         : "✅ Welcome message updated.",
    "write_welcome"       : "✍️ Write the welcome message:\n(You can use {name} and {badge})",
    "write_id"            : "✍️ Type the user ID and send:",
    "write_ch"            : "✍️ Type the channel username (e.g. @mychannel):",
    "ask_link_prompt"     : "🔗 Please send me an Instagram link:",
    "vip_yes"             : "Yes 💎",
    "vip_no"              : "No",
    "badge_owner"         : "👑",
    "badge_super"         : "🌌",
    "badge_admin"         : "🛡",
    "badge_vip"           : "💎",
    "b_dl"                : "📥 New Download",
    "b_profile"           : "👤 My Profile",
    "b_vip"               : "💎 VIP Section",
    "b_settings"          : "⚙️ Settings & Language",
    "b_help"              : "ℹ️ Help",
    "b_channel"           : "📢 Bot Channel",
    "b_panel"             : "⚙️ Control Panel",
    "b_back"              : "🔙 Back",
    "b_delete"            : "🗑 Delete",
    "b_joined"            : "✅ I Joined",
    "b_video"             : "🎥 Video (No Watermark)",
    "b_photos"            : "📸 Photos ({n})",
    "b_audio"             : "🎵 Audio (MP3)",
    "b_ku"                : "🔴🔆🟢 کوردی",
    "b_en"                : "🇺🇸 English",
    "b_ar"                : "🇸🇦 العربية",
    "b_cancel"            : "❌ Cancel",
    "b_confirm_remove"    : "✅ Yes, Remove",
    "b_cancel_remove"     : "❌ No, Cancel",
    "confirm_remove_admin": "⚠️ Remove this admin?\n🆔 {id}",
    "confirm_remove_super": "⚠️ Remove this super admin?\n🆔 {id}",
    "confirm_remove_ch"   : "⚠️ Remove this channel?\n{ch}",
    "unified_panel_title" : "⚙️ Control Panel\n\n👥 Users: {users}\n💎 VIP: {vip}\n🚫 Blocked: {blocked}\n📥 Downloads: {dl}\n⏱ Uptime: {uptime}",
    "adm_stats_title"     : "📊 Stats:\n👥 Total users: {users}\n💎 VIP: {vip}\n🚫 Blocked: {blocked}\n📥 Downloads: {dl}\n⏱ Uptime: {uptime}",
    "adm_broadcast_ask"   : "✍️ Send your message (text, photo, video):",
    "adm_block_ask"       : "🚫 Block User:\n\n{write_id}",
    "adm_info_ask"        : "👤 User Info:\n\n{write_id}",
    "b_adm_stats"         : "📊 Stats",
    "b_adm_broadcast"     : "📢 Broadcast",
    "b_adm_block"         : "🚫 Block User",
    "b_adm_info"          : "👤 User Info",
    "b_adm_admins"        : "👮 Admins",
    "sup_panel_title"     : "🌌 Super Section",
    "sup_maint_on"        : "🔴 ON",
    "sup_maint_off"       : "🟢 OFF",
    "sup_admins_title"    : "👮 Admins ({count}):",
    "sup_vip_title"       : "💎 VIP ({count}):",
    "sup_ch_title"        : "📢 Channels ({count}):",
    "sup_ch_empty"        : "📭 Empty",
    "sup_ch_remove_q"     : "Which channel to remove?",
    "sup_ch_added"        : "✅ {ch} added!",
    "sup_add_adm_ask"     : "➕ Add Admin:\n\n{write_id}",
    "sup_rm_adm_ask"      : "➖ Remove Admin:\n\n{write_id}",
    "sup_add_vip_ask"     : "💎 Give VIP:\n\n{write_id}",
    "sup_rm_vip_ask"      : "➖ Remove VIP:\n\n{write_id}",
    "sup_add_ch_ask"      : "📢 Add Channel:\n\n{write_ch}",
    "b_sup_admins"        : "👮 Admins",
    "b_sup_vip"           : "💎 VIP",
    "b_sup_channels"      : "📢 Channels",
    "b_sup_maint"         : "🛠 Maintenance: {status}",
    "b_sup_botlang"       : "🌍 Bot Language",
    "b_add"               : "➕ Add",
    "b_remove"            : "➖ Remove",
    "b_add_vip"           : "➕ VIP",
    "b_rm_vip"            : "➖ VIP",
    "b_refresh"           : "🔄 Refresh",
    "b_clear"             : "🗑 Clear",
    "own_panel_title"     : "👑 Owner Section",
    "own_super_title"     : "🌌 Super Admins ({count}):",
    "own_add_sup_ask"     : "➕ Add Super Admin:\n\n{write_id}",
    "own_rm_sup_ask"      : "➖ Remove Super Admin:\n\n{write_id}",
    "b_own_super"         : "🌌 Super Admins",
    "b_own_botlang"       : "🌍 Bot Language",
    "b_own_welcome"       : "📝 Welcome Message",
    "b_own_reset"         : "🗑 Reset Stats",
    "b_own_backup"        : "💾 Backup",
    "own_reset_done"      : "✅ Stats have been reset!",
    "own_backup_prep"     : "⏳ Preparing...",
    "new_user_notify"     : "🔔 New User!\n\n👤 Name: {name}\n🔗 User: {uname}\n🆔 ID: {uid}\n🌐 App Lang: {app_lang}\n📅 {date}",
    "b_notify_block"      : "🚫 Block",
    "b_notify_vip"        : "💎 VIP",
    "b_notify_admin"      : "🛡 Admin",
    "b_notify_info"       : "👤 Info",
    "act_blocked"         : "🚫 {id} has been blocked!",
    "act_unblocked"       : "✅ {id} has been unblocked.",
    "act_adm_added"       : "✅ {id} is now Admin!",
    "act_adm_removed"     : "➖ {id} removed from Admin.",
    "act_sup_added"       : "🌌 {id} is now Super Admin!",
    "act_sup_removed"     : "➖ {id} removed from Super Admin.",
    "act_vip_added"       : "💎 {id} is now VIP!",
    "act_vip_removed"     : "➖ VIP removed from {id}.",
    "act_ch_wrong_fmt"    : "❌ Wrong format! Use: @channelname",
    "userinfo_text"       : "👤 Name: {name}\n🔗 User: @{user}\n🆔 ID: {id}\n💎 VIP: {vip}\n🌍 Lang: {lang}\n📥 Downloads: {dl}\n📅 Joined: {date}",
},
"ar": {
    "welcome"             : "👋 مرحباً {name} {badge}\n\n📸 أهلاً بك في أفضل بوت انستغرام!\n📥 حمّل الفيديوهات والصور والصوت بأعلى سرعة.\n\n━━━━━━━━━━━━━━━━━━━\n👇 أرسل لي رابط انستغرام:",
    "help"                : "📚 كيفية الاستخدام\n\n1️⃣ انسخ رابط الفيديو من انستغرام.\n2️⃣ الصقه هنا.\n3️⃣ اختر نوع التنزيل!\n\n🎥 فيديو: بدون علامة.\n📸 صور.\n🎵 صوت: MP3.\n\n💎 VIP: بدون اشتراك.\n📩 للتواصل: {dev}",
    "profile"             : "👤 بطاقة الملف\n\n🆔 المعرف: {id}\n👤 الاسم: {name}\n🔗 اسم المستخدم: @{user}\n📅 تاريخ التسجيل: {date}\n💎 VIP: {vip}\n🌍 اللغة: {ulang}\n📥 التنزيلات: {dl}",
    "vip_info"            : "💎 مميزات VIP\n\n✅ تخطي الاشتراك الإجباري.\n✅ سرعة تنزيل أعلى.\n\nلشراء VIP: {dev}",
    "lang_title"          : "🌍 اختر لغتك:",
    "lang_saved"          : "✅ تم تغيير اللغة!",
    "bot_lang_title"      : "🌍 اختر اللغة الافتراضية للبوت:",
    "bot_lang_saved"      : "✅ تم تغيير اللغة الافتراضية إلى: {lang}",
    "bot_lang_current"    : "🔵 الحالي: {cur}",
    "force_join"          : "🔒 الاشتراك الإجباري\nيرجى الانضمام إلى هذه القنوات أولاً، ثم اضغط '✅ انضممت':",
    "found"               : "📝 العنوان: {title}\n👤 المالك: {owner}\n\n📊 الإحصائيات:\n👁 مشاهدة: {views}  \n❤️ إعجاب: {likes}  \n💬 تعليق: {comments}\n\n🎬 <a href=\"https://t.me/Instagram_Downloader_Jack_Robot\">اضغط هنا — ابدأ التحميل</a>",
    "sending_photos"      : "📸 جاري تجهيز الصور...",
    "blocked_msg"         : "⛔ أنت محظور.",
    "maintenance_msg"     : "🛠 صيانة!\n\n⚙️ البوت تحت تحديث.\n⏳ سنعود قريباً!\n\n📩 للتواصل: {dev}",
    "session_expired"     : "⚠️ انتهت الجلسة! أرسل الرابط مجدداً.",
    "invalid_link"        : "❌ الرابط غير صحيح أو غير موجود!",
    "dl_fail"             : "❌ حدث خطأ! تعذر التنزيل.",
    "no_photo"            : "❌ هذا المنشور لا يحتوي على صور!",
    "no_video"            : "❌ الفيديو غير موجود!",
    "no_audio"            : "❌ الصوت غير متاح!",
    "invalid_id"          : "❌ معرف غير صحيح! أرقام فقط.",
    "user_not_found"      : "⚠️ المستخدم غير موجود.",
    "broadcast_done"      : "📢 اكتمل الإرسال\n✅ تم: {ok}\n❌ فشل: {fail}",
    "broadcast_sending"   : "⏳ جاري الإرسال لـ {total} مستخدم...",
    "broadcast_progress"  : "⏳ الإرسال: {done}/{total}...",
    "welcome_set"         : "✅ تم تحديث رسالة الترحيب.",
    "write_welcome"       : "✍️ اكتب رسالة الترحيب:\n(يمكنك استخدام {name} و {badge})",
    "write_id"            : "✍️ أرسل معرف المستخدم:",
    "write_ch"            : "✍️ أرسل اسم القناة (مثال: @mychannel):",
    "ask_link_prompt"     : "🔗 يرجى إرسال رابط انستغرام:",
    "vip_yes"             : "نعم 💎",
    "vip_no"              : "لا",
    "badge_owner"         : "👑",
    "badge_super"         : "🌌",
    "badge_admin"         : "🛡",
    "badge_vip"           : "💎",
    "b_dl"                : "📥 تنزيل جديد",
    "b_profile"           : "👤 ملفي الشخصي",
    "b_vip"               : "💎 قسم VIP",
    "b_settings"          : "⚙️ الإعدادات واللغة",
    "b_help"              : "ℹ️ مساعدة",
    "b_channel"           : "📢 قناة البوت",
    "b_panel"             : "⚙️ لوحة التحكم",
    "b_back"              : "🔙 رجوع",
    "b_delete"            : "🗑 حذف",
    "b_joined"            : "✅ انضممت",
    "b_video"             : "🎥 فيديو (بدون علامة)",
    "b_photos"            : "📸 الصور ({n})",
    "b_audio"             : "🎵 الصوت (MP3)",
    "b_ku"                : "🔴🔆🟢 کوردی",
    "b_en"                : "🇺🇸 English",
    "b_ar"                : "🇸🇦 العربية",
    "b_cancel"            : "❌ إلغاء",
    "b_confirm_remove"    : "✅ نعم، احذف",
    "b_cancel_remove"     : "❌ لا، إلغاء",
    "confirm_remove_admin": "⚠️ حذف هذا المشرف؟\n🆔 {id}",
    "confirm_remove_super": "⚠️ حذف هذا السوبر مشرف؟\n🆔 {id}",
    "confirm_remove_ch"   : "⚠️ حذف هذه القناة؟\n{ch}",
    "unified_panel_title" : "⚙️ لوحة التحكم\n\n👥 المستخدمون: {users}\n💎 VIP: {vip}\n🚫 المحظورون: {blocked}\n📥 التنزيلات: {dl}\n⏱ وقت التشغيل: {uptime}",
    "adm_stats_title"     : "📊 الإحصائيات:\n👥 إجمالي: {users}\n💎 VIP: {vip}\n🚫 محظور: {blocked}\n📥 تنزيلات: {dl}\n⏱ وقت: {uptime}",
    "adm_broadcast_ask"   : "✍️ أرسل رسالتك (نص، صورة، فيديو):",
    "adm_block_ask"       : "🚫 حظر مستخدم:\n\n{write_id}",
    "adm_info_ask"        : "👤 معلومات المستخدم:\n\n{write_id}",
    "b_adm_stats"         : "📊 الإحصائيات",
    "b_adm_broadcast"     : "📢 إرسال جماعي",
    "b_adm_block"         : "🚫 حظر",
    "b_adm_info"          : "👤 معلومات مستخدم",
    "b_adm_admins"        : "👮 المشرفون",
    "sup_panel_title"     : "🌌 القسم الخاص",
    "sup_maint_on"        : "🔴 مفعل",
    "sup_maint_off"       : "🟢 معطل",
    "sup_admins_title"    : "👮 المشرفون ({count}):",
    "sup_vip_title"       : "💎 VIP ({count}):",
    "sup_ch_title"        : "📢 القنوات ({count}):",
    "sup_ch_empty"        : "📭 فارغ",
    "sup_ch_remove_q"     : "أي قناة تريد حذفها؟",
    "sup_ch_added"        : "✅ {ch} تمت الإضافة!",
    "sup_add_adm_ask"     : "➕ مشرف جديد:\n\n{write_id}",
    "sup_rm_adm_ask"      : "➖ إزالة مشرف:\n\n{write_id}",
    "sup_add_vip_ask"     : "💎 منح VIP:\n\n{write_id}",
    "sup_rm_vip_ask"      : "➖ إزالة VIP:\n\n{write_id}",
    "sup_add_ch_ask"      : "📢 إضافة قناة:\n\n{write_ch}",
    "b_sup_admins"        : "👮 المشرفون",
    "b_sup_vip"           : "💎 VIP",
    "b_sup_channels"      : "📢 القنوات",
    "b_sup_maint"         : "🛠 الصيانة: {status}",
    "b_sup_botlang"       : "🌍 لغة البوت",
    "b_add"               : "➕ إضافة",
    "b_remove"            : "➖ حذف",
    "b_add_vip"           : "➕ VIP",
    "b_rm_vip"            : "➖ VIP",
    "b_refresh"           : "🔄 تحديث",
    "b_clear"             : "🗑 مسح",
    "own_panel_title"     : "👑 قسم المالك",
    "own_super_title"     : "🌌 السوبر مشرفون ({count}):",
    "own_add_sup_ask"     : "➕ سوبر مشرف جديد:\n\n{write_id}",
    "own_rm_sup_ask"      : "➖ إزالة سوبر مشرف:\n\n{write_id}",
    "b_own_super"         : "🌌 السوبر مشرفون",
    "b_own_botlang"       : "🌍 لغة البوت",
    "b_own_welcome"       : "📝 رسالة الترحيب",
    "b_own_reset"         : "🗑 إعادة الإحصائيات",
    "b_own_backup"        : "💾 نسخة احتياطية",
    "own_reset_done"      : "✅ تم إعادة الإحصائيات!",
    "own_backup_prep"     : "⏳ جاري التجهيز...",
    "new_user_notify"     : "🔔 مستخدم جديد!\n\n👤 الاسم: {name}\n🔗 المعرف: {uname}\n🆔 ID: {uid}\n🌐 لغة التطبيق: {app_lang}\n📅 {date}",
    "b_notify_block"      : "🚫 حظر",
    "b_notify_vip"        : "💎 VIP",
    "b_notify_admin"      : "🛡 مشرف",
    "b_notify_info"       : "👤 معلومات",
    "act_blocked"         : "🚫 {id} تم الحظر!",
    "act_unblocked"       : "✅ {id} تم رفع الحظر.",
    "act_adm_added"       : "✅ {id} أصبح مشرفاً!",
    "act_adm_removed"     : "➖ {id} أُزيل من المشرفين.",
    "act_sup_added"       : "🌌 {id} أصبح سوبر مشرف!",
    "act_sup_removed"     : "➖ {id} أُزيل من السوبر مشرفين.",
    "act_vip_added"       : "💎 {id} أصبح VIP!",
    "act_vip_removed"     : "➖ تم إزالة VIP من {id}.",
    "act_ch_wrong_fmt"    : "❌ صيغة خاطئة! استخدم: @channelname",
    "userinfo_text"       : "👤 الاسم: {name}\n🔗 المعرف: @{user}\n🆔 ID: {id}\n💎 VIP: {vip}\n🌍 اللغة: {lang}\n📥 تنزيلات: {dl}\n📅 تاريخ: {date}",
},
}

LANG_NAMES = {"ku": "کوردی", "en": "English", "ar": "العربية"}

# ==============================================================================
# ── 3. UTILS & DATABASE
# ==============================================================================
def tx(lang: str, key: str, **kw) -> str:
    base = L.get(lang, L["ku"])
    text = base.get(key, L["ku"].get(key, key))
    try:    return text.format(**kw)
    except: return text

def clean_title(t: str) -> str:
    return re.sub(r'[\/*?:"<>|#]', "", str(t))[:100].strip() or "No Title"

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
        super_admins_set = set(d.get("super_admins", [OWNER_ID] if OWNER_ID else []))
        admins_set       = set(d.get("admins",       [OWNER_ID] if OWNER_ID else []))
        channels_list    = d.get("channels", [])
        blocked_set      = set(d.get("blocked", []))
        vip_set          = set(d.get("vips",    []))
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
            if m.status in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED):
                missing.append(ch)
        except: missing.append(ch)
    return len(missing) == 0, missing

# ==============================================================================
# ── 4. INSTAGRAM SCRAPER
# ==============================================================================
def get_post_id(url: str) -> str | None:
    m = re.search(r"instagram\.com/(?:p|reel|reels)/([A-Za-z0-9_-]+)", url)
    return m.group(1) if m else None

async def fetch_instagram(url: str) -> dict | None:
    post_id = get_post_id(url)
    if not post_id: return None
    timeout = int(CFG.get("api_timeout", 60))
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"}

    async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as c:
        # Method 1: Instagram GraphQL
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
                "variables": variables, "server_timestamps": "true",
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
                d = r.json()
                media = d.get("data", {}).get("xdt_shortcode_media", {})
                if media:
                    owner    = media.get("owner", {}).get("username", "Instagram User")
                    edges    = media.get("edge_media_to_caption", {}).get("edges", [])
                    title    = edges[0].get("node", {}).get("text", "Instagram Post") if edges else "Instagram Post"
                    views    = media.get("video_view_count") or media.get("play_count") or 0
                    likes    = media.get("edge_media_preview_like", {}).get("count") or 0
                    comments = media.get("edge_media_to_comment", {}).get("count") or 0

                    audio_url = None
                    clips = media.get("clips_metadata") or {}
                    orig  = clips.get("original_sound_info") or {}
                    if orig.get("progressive_download_url"):
                        audio_url = orig["progressive_download_url"]
                    if not audio_url:
                        asset = (clips.get("music_info") or {}).get("music_asset_info") or {}
                        if asset.get("progressive_download_url"):
                            audio_url = asset["progressive_download_url"]

                    video_url = media.get("video_url")
                    images = []
                    if media.get("edge_sidecar_to_children"):
                        for edge in media["edge_sidecar_to_children"].get("edges", []):
                            node = edge.get("node", {})
                            if node.get("is_video"):
                                if not video_url: video_url = node.get("video_url")
                            else:
                                img = node.get("display_url")
                                if img: images.append(img)
                    elif not media.get("is_video"):
                        img = media.get("display_url")
                        if img: images.append(img)

                    return {
                        "video_url": video_url, "images": images, "audio_url": audio_url,
                        "title": clean_title(title), "creator": owner, "owner": owner,
                        "views": views, "likes": likes, "comments": comments,
                    }
        except: pass

        # Method 2: Fallback API
        try:
            r = await c.get(f"https://api.instadownloader.org/v1?url=https://www.instagram.com/p/{post_id}/")
            if r.status_code == 200:
                d = r.json()
                if d.get("video"):
                    return {
                        "video_url": d["video"], "images": [], "audio_url": None,
                        "title": "Instagram Post", "creator": "Instagram", "owner": "Instagram",
                        "views": 0, "likes": 0, "comments": 0,
                    }
        except: pass

    return None

# ==============================================================================
# ── 5. UI HELPERS
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
# ── 6. HANDLERS
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
            "name": user.first_name, "user": user.username or "",
            "date": now_str(), "vip": False, "dl": 0,
            "lang": CFG.get("default_lang", "ku"),
        })
        if OWNER_ID:
            uname = f"@{user.username}" if user.username else "—"
            notify_text = tx("ku", "new_user_notify",
                name=html.escape(user.first_name), uname=uname, uid=uid,
                app_lang=user.language_code or "—", date=now_str()
            )
            notify_kb = InlineKeyboardMarkup([
                [InlineKeyboardButton(tx("ku", "b_notify_block"), callback_data=f"quick_blk_{uid}"),
                 InlineKeyboardButton(tx("ku", "b_notify_vip"),   callback_data=f"quick_vip_{uid}")],
                [InlineKeyboardButton(tx("ku", "b_notify_admin"), callback_data=f"quick_adm_{uid}"),
                 InlineKeyboardButton(tx("ku", "b_notify_info"),  callback_data=f"quick_inf_{uid}")],
            ])
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
        await update.message.reply_text("✅ PONG! Bot is alive.")

async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    data = q.data
    uid  = q.from_user.id
    lang = await get_user_lang(uid)
    try: await q.answer()
    except: pass

    # ── Quick actions ──────────────────────────────────────────────────────────
    if data.startswith("quick_") and is_owner(uid):
        parts = data.split("_"); action = parts[1]; tid = int(parts[2])
        if action == "blk":
            blocked_set.add(tid); await save_cfg()
            await q.answer(tx("ku", "act_blocked", id=tid), show_alert=True); return
        if action == "vip":
            vip_set.add(tid); await user_field(tid, "vip", True); await save_cfg()
            await q.answer(tx("ku", "act_vip_added", id=tid), show_alert=True); return
        if action == "adm":
            admins_set.add(tid); await save_cfg()
            await q.answer(tx("ku", "act_adm_added", id=tid), show_alert=True); return
        if action == "inf":
            ud = await user_get(tid)
            if not ud: await q.answer(tx("ku", "user_not_found"), show_alert=True); return
            info = tx("ku", "userinfo_text", name=ud.get("name","—"), user=ud.get("user","—"),
                id=tid, vip=tx("ku","vip_yes") if ud.get("vip") else tx("ku","vip_no"),
                lang=ud.get("lang","—"), dl=ud.get("dl",0), date=ud.get("date","—"))
            await q.answer(info[:200], show_alert=True); return

    # ── Navigation ─────────────────────────────────────────────────────────────
    if data in ("main_menu_render", "check_join_btn"):
        ok_sub, _ = await check_join(uid, ctx)
        if not ok_sub and not bypass_join(uid): return
        text, markup = await render_main_menu(uid, lang, q.from_user.first_name)
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=markup); return

    if data == "close":
        try: await q.message.delete()
        except: pass
        return

    if data == "ask_link":
        await q.message.reply_text(tx(lang, "ask_link_prompt"), reply_markup=ForceReply(selective=True))
        return

    if data == "show_profile":
        ud = await user_get(uid) or {}
        ulang_str = LANG_NAMES.get(ud.get("lang", CFG.get("default_lang", "ku")), "?")
        text = tx(lang, "profile", id=uid, name=html.escape(q.from_user.first_name),
            user=q.from_user.username or "—", date=ud.get("date","—"),
            vip=tx(lang,"vip_yes") if is_vip(uid) else tx(lang,"vip_no"),
            ulang=ulang_str, dl=ud.get("dl",0))
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(back(lang))); return

    if data == "show_vip":
        await q.edit_message_text(tx(lang,"vip_info",dev=DEV), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(back(lang))); return

    if data == "show_help":
        await q.edit_message_text(tx(lang,"help",dev=DEV), parse_mode="HTML", reply_markup=InlineKeyboardMarkup(back(lang))); return

    if data == "show_settings":
        cur = LANG_NAMES.get(lang, "?")
        await q.edit_message_text(tx(lang,"lang_title") + f"\n\n🔵 {cur}",
            reply_markup=InlineKeyboardMarkup(lang_select_buttons() + back(lang))); return

    if data.startswith("set_lang_"):
        chosen = data.split("_")[2]
        await user_field(uid, "lang", chosen)
        text, markup = await render_main_menu(uid, chosen, q.from_user.first_name)
        await q.edit_message_text(text, parse_mode="HTML", reply_markup=markup); return

    if data.startswith("set_bot_lang_") and is_super(uid):
        chosen = data.split("_")[3]
        CFG["default_lang"] = chosen; await save_cfg()
        await q.answer(tx(lang,"bot_lang_saved",lang=LANG_NAMES.get(chosen,chosen)), show_alert=True)
        q.data = "panel_unified"; await on_callback(update, ctx); return

    # ── Download — TikTok style session ───────────────────────────────────────
    if data.startswith("dl_"):
        sess = await session_get(uid)
        if not sess: await q.answer(tx(lang,"session_expired"), show_alert=True); return

        cap    = f"📸 {html.escape(sess.get('title',''))}\n👤 {html.escape(sess.get('creator', sess.get('owner','')))}\n\n🎬 <a href='https://t.me/Instagram_Downloader_Jack_Robot'>کلیک لێرە بکە — دابەزاندن دەستپێبکە</a>"
        del_kb = InlineKeyboardMarkup([[InlineKeyboardButton(tx(lang,"b_delete"), callback_data="close")]])

        if data == "dl_photo":
            imgs = sess.get("images", [])
            if not imgs: await q.answer(tx(lang,"no_photo"), show_alert=True); return
            try: await q.message.delete()
            except: pass
            w = await ctx.bot.send_message(uid, tx(lang,"sending_photos"))
            for i in range(0, min(len(imgs), int(CFG.get("max_photos",15))), 10):
                chunk = imgs[i:i+10]
                media = [InputMediaPhoto(u) for u in chunk]
                if i == 0: media[0].caption = cap; media[0].parse_mode = "HTML"
                try: await ctx.bot.send_media_group(uid, media)
                except:
                    for u in chunk:
                        try: await ctx.bot.send_photo(uid, u)
                        except: pass
                await asyncio.sleep(1)
            try: await w.delete()
            except: pass

        elif data == "dl_video":
            vurl = sess.get("video_url")
            if not vurl: await q.answer(tx(lang,"no_video"), show_alert=True); return
            try: await q.message.delete()
            except: pass
            try: await ctx.bot.send_video(uid, vurl, caption=cap, parse_mode="HTML", reply_markup=del_kb)
            except: await ctx.bot.send_message(uid, f"{cap}\n📥 <a href='{vurl}'>Link</a>", parse_mode="HTML", reply_markup=del_kb)

        elif data == "dl_audio":
            aurl = sess.get("audio_url")
            if not aurl: await q.answer(tx(lang,"no_audio"), show_alert=True); return
            try: await q.message.delete()
            except: pass
            try: await ctx.bot.send_audio(uid, aurl, caption=cap, parse_mode="HTML", title="Instagram Audio", performer="Instagram", reply_markup=del_kb)
            except: await ctx.bot.send_message(uid, f"{cap}\n🎵 <a href='{aurl}'>Link</a>", parse_mode="HTML", reply_markup=del_kb)

        CFG["total_dl"] = CFG.get("total_dl", 0) + 1
        await save_cfg()
        ud = await user_get(uid) or {}
        await user_field(uid, "dl", ud.get("dl", 0) + 1)
        return

    # ── Unified Panel ──────────────────────────────────────────────────────────
    if data == "panel_unified":
        if not is_admin(uid): return
        uids_list = await all_uids()
        kb = []
        kb.append([InlineKeyboardButton(tx(lang,"b_adm_stats"),     callback_data="adm_stats"),
                   InlineKeyboardButton(tx(lang,"b_adm_broadcast"), callback_data="adm_broadcast")])
        kb.append([InlineKeyboardButton(tx(lang,"b_adm_block"),  callback_data="adm_block"),
                   InlineKeyboardButton(tx(lang,"b_adm_info"),   callback_data="adm_userinfo")])
        kb.append([InlineKeyboardButton(tx(lang,"b_adm_admins"), callback_data="adm_manage_admins")])
        if is_super(uid):
            kb.append([InlineKeyboardButton("─── 🌌 Super ───", callback_data="noop")])
            kb.append([InlineKeyboardButton(tx(lang,"b_sup_vip"),      callback_data="sup_vips"),
                       InlineKeyboardButton(tx(lang,"b_sup_channels"), callback_data="sup_channels")])
            maint_status = tx(lang,"sup_maint_on") if CFG["maintenance"] else tx(lang,"sup_maint_off")
            kb.append([InlineKeyboardButton(tx(lang,"b_sup_maint",status=maint_status), callback_data="sup_toggle_maint"),
                       InlineKeyboardButton(tx(lang,"b_sup_botlang"), callback_data="sup_bot_lang")])
        if is_owner(uid):
            kb.append([InlineKeyboardButton("─── 👑 Owner ───", callback_data="noop")])
            kb.append([InlineKeyboardButton(tx(lang,"b_own_super"),   callback_data="own_super_adms"),
                       InlineKeyboardButton(tx(lang,"b_own_welcome"), callback_data="own_welcome")])
            kb.append([InlineKeyboardButton(tx(lang,"b_own_reset"),  callback_data="own_reset_stats"),
                       InlineKeyboardButton(tx(lang,"b_own_backup"), callback_data="own_backup")])
        kb += back(lang)
        await q.edit_message_text(
            tx(lang,"unified_panel_title", users=len(uids_list), vip=len(vip_set),
               blocked=len(blocked_set), dl=fmt(CFG.get("total_dl",0)), uptime=uptime()),
            reply_markup=InlineKeyboardMarkup(kb)); return

    if data == "noop": return

    # ── Admin Section ──────────────────────────────────────────────────────────
    if data.startswith("adm_"):
        if not is_admin(uid): return

        if data == "adm_stats":
            await q.edit_message_text(
                tx(lang,"adm_stats_title", users=len(await all_uids()), vip=len(vip_set),
                   blocked=len(blocked_set), dl=fmt(CFG.get("total_dl",0)), uptime=uptime()),
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton(tx(lang,"b_refresh"), callback_data="adm_stats")],
                     *back(lang,"panel_unified")])); return

        if data == "adm_broadcast":
            waiting_state[uid] = "broadcast_all"
            await q.edit_message_text(tx(lang,"adm_broadcast_ask"),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx(lang,"b_cancel"), callback_data="panel_unified")]])); return

        if data == "adm_block":
            waiting_state[uid] = "action_blk_add"
            await q.edit_message_text(tx(lang,"adm_block_ask", write_id=tx(lang,"write_id")),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx(lang,"b_cancel"), callback_data="panel_unified")]])); return

        if data == "adm_userinfo":
            waiting_state[uid] = "action_info_check"
            await q.edit_message_text(tx(lang,"adm_info_ask", write_id=tx(lang,"write_id")),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx(lang,"b_cancel"), callback_data="panel_unified")]])); return

        if data == "adm_manage_admins":
            adm_real = admins_set - super_admins_set
            lines = [await get_user_display(a) for a in adm_real]
            text = tx(lang,"sup_admins_title", count=len(adm_real))
            if lines: text += "\n" + "\n".join(f"• {l}" for l in lines)
            kb = [[InlineKeyboardButton(tx(lang,"b_add"),    callback_data="adm_add_admin"),
                   InlineKeyboardButton(tx(lang,"b_remove"), callback_data="adm_rm_admin_list")],
                  *back(lang,"panel_unified")]
            await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb)); return

        if data == "adm_add_admin":
            waiting_state[uid] = "action_adm_add"
            await q.edit_message_text(tx(lang,"sup_add_adm_ask", write_id=tx(lang,"write_id")),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx(lang,"b_cancel"), callback_data="adm_manage_admins")]])); return

        if data == "adm_rm_admin_list":
            adm_real = admins_set - super_admins_set
            if not adm_real: await q.answer("—", show_alert=True); return
            kb = [[InlineKeyboardButton(f"❌ {await get_user_display(a)}", callback_data=f"adm_confirm_rm_{a}")] for a in adm_real]
            kb += back(lang,"adm_manage_admins")
            await q.edit_message_text(tx(lang,"sup_admins_title", count=len(adm_real)), reply_markup=InlineKeyboardMarkup(kb)); return

        if data.startswith("adm_confirm_rm_"):
            aid = int(data.split("_")[3])
            await q.edit_message_text(tx(lang,"confirm_remove_admin", id=aid),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(tx(lang,"b_confirm_remove"), callback_data=f"adm_do_rm_{aid}")],
                    [InlineKeyboardButton(tx(lang,"b_cancel_remove"),  callback_data="adm_manage_admins")]])); return

        if data.startswith("adm_do_rm_"):
            aid = int(data.split("_")[3])
            admins_set.discard(aid); await save_cfg()
            await q.answer(tx(lang,"act_adm_removed", id=aid), show_alert=True)
            q.data = "adm_manage_admins"; await on_callback(update, ctx); return

    # ── Super Section ──────────────────────────────────────────────────────────
    if data.startswith("sup_"):
        if not is_super(uid): return

        if data == "sup_toggle_maint":
            CFG["maintenance"] = not CFG["maintenance"]; await save_cfg()
            await q.answer(f"🛠 {'ON' if CFG['maintenance'] else 'OFF'}", show_alert=True)
            q.data = "panel_unified"; await on_callback(update, ctx); return

        if data == "sup_bot_lang":
            cur = LANG_NAMES.get(CFG.get("default_lang","ku"),"?")
            await q.edit_message_text(tx(lang,"bot_lang_title") + f"\n\n{tx(lang,'bot_lang_current',cur=cur)}",
                reply_markup=InlineKeyboardMarkup(bot_lang_select_buttons() + back(lang,"panel_unified"))); return

        if data == "sup_vips":
            lines = [await get_user_display(v) for v in vip_set]
            text = tx(lang,"sup_vip_title", count=len(vip_set))
            if lines: text += "\n" + "\n".join(f"• {l}" for l in lines)
            kb = [[InlineKeyboardButton(tx(lang,"b_add_vip"), callback_data="sup_add_vip"),
                   InlineKeyboardButton(tx(lang,"b_rm_vip"),  callback_data="sup_rm_vip_list")],
                  *back(lang,"panel_unified")]
            await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb)); return

        if data == "sup_add_vip":
            waiting_state[uid] = "action_vip_add"
            await q.edit_message_text(tx(lang,"sup_add_vip_ask", write_id=tx(lang,"write_id")),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx(lang,"b_cancel"), callback_data="sup_vips")]])); return

        if data == "sup_rm_vip_list":
            if not vip_set: await q.answer(tx(lang,"sup_ch_empty"), show_alert=True); return
            kb = [[InlineKeyboardButton(f"❌ {await get_user_display(v)}", callback_data=f"sup_do_rm_vip_{v}")] for v in vip_set]
            kb += back(lang,"sup_vips")
            await q.edit_message_text(tx(lang,"sup_vip_title",count=len(vip_set)), reply_markup=InlineKeyboardMarkup(kb)); return

        if data.startswith("sup_do_rm_vip_"):
            vid = int(data.split("_")[4])
            vip_set.discard(vid); await user_field(vid,"vip",False); await save_cfg()
            await q.answer(tx(lang,"act_vip_removed",id=vid), show_alert=True)
            q.data = "sup_vips"; await on_callback(update, ctx); return

        if data == "sup_channels":
            ch_text = "\n".join(channels_list) if channels_list else tx(lang,"sup_ch_empty")
            kb = [[InlineKeyboardButton(tx(lang,"b_add"),    callback_data="sup_add_ch"),
                   InlineKeyboardButton(tx(lang,"b_remove"), callback_data="sup_rm_ch_list")],
                  *back(lang,"panel_unified")]
            await q.edit_message_text(tx(lang,"sup_ch_title",count=len(channels_list)) + f"\n{ch_text}",
                reply_markup=InlineKeyboardMarkup(kb)); return

        if data == "sup_add_ch":
            waiting_state[uid] = "action_add_ch"
            await q.edit_message_text(tx(lang,"sup_add_ch_ask",write_ch=tx(lang,"write_ch")),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx(lang,"b_cancel"), callback_data="sup_channels")]])); return

        if data == "sup_rm_ch_list":
            if not channels_list: await q.answer(tx(lang,"sup_ch_empty"), show_alert=True); return
            kb = [[InlineKeyboardButton(f"❌ {c}", callback_data=f"sup_confirm_rm_ch_{c}")] for c in channels_list]
            kb += back(lang,"sup_channels")
            await q.edit_message_text(tx(lang,"sup_ch_remove_q"), reply_markup=InlineKeyboardMarkup(kb)); return

        if data.startswith("sup_confirm_rm_ch_"):
            ch = data[len("sup_confirm_rm_ch_"):]
            await q.edit_message_text(tx(lang,"confirm_remove_ch",ch=ch),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(tx(lang,"b_confirm_remove"), callback_data=f"sup_do_rm_ch_{ch}")],
                    [InlineKeyboardButton(tx(lang,"b_cancel_remove"),  callback_data="sup_channels")]])); return

        if data.startswith("sup_do_rm_ch_"):
            ch = data[len("sup_do_rm_ch_"):]
            if ch in channels_list: channels_list.remove(ch); await save_cfg()
            q.data = "sup_channels"; await on_callback(update, ctx); return

    # ── Owner Section ──────────────────────────────────────────────────────────
    if data.startswith("own_"):
        if not is_owner(uid): return

        if data == "own_super_adms":
            sup_real = super_admins_set - {OWNER_ID}
            lines = [await get_user_display(s) for s in sup_real]
            text = tx(lang,"own_super_title", count=len(sup_real))
            if lines: text += "\n" + "\n".join(f"• {l}" for l in lines)
            kb = [[InlineKeyboardButton(tx(lang,"b_add"),    callback_data="own_add_sup"),
                   InlineKeyboardButton(tx(lang,"b_remove"), callback_data="own_rm_sup_list")],
                  *back(lang,"panel_unified")]
            await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb)); return

        if data == "own_add_sup":
            waiting_state[uid] = "action_sup_add"
            await q.edit_message_text(tx(lang,"own_add_sup_ask",write_id=tx(lang,"write_id")),
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(tx(lang,"b_cancel"), callback_data="own_super_adms")]])); return

        if data == "own_rm_sup_list":
            sup_real = super_admins_set - {OWNER_ID}
            if not sup_real: await q.answer("—", show_alert=True); return
            kb = [[InlineKeyboardButton(f"❌ {await get_user_display(s)}", callback_data=f"own_confirm_rm_sup_{s}")] for s in sup_real]
            kb += back(lang,"own_super_adms")
            await q.edit_message_text(tx(lang,"own_super_title",count=len(sup_real)), reply_markup=InlineKeyboardMarkup(kb)); return

        if data.startswith("own_confirm_rm_sup_"):
            sid = int(data.split("_")[4])
            await q.edit_message_text(tx(lang,"confirm_remove_super",id=sid),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(tx(lang,"b_confirm_remove"), callback_data=f"own_do_rm_sup_{sid}")],
                    [InlineKeyboardButton(tx(lang,"b_cancel_remove"),  callback_data="own_super_adms")]])); return

        if data.startswith("own_do_rm_sup_"):
            sid = int(data.split("_")[4])
            super_admins_set.discard(sid); await save_cfg()
            await q.answer(tx(lang,"act_sup_removed",id=sid), show_alert=True)
            q.data = "own_super_adms"; await on_callback(update, ctx); return

        if data == "own_welcome":
            waiting_state[uid] = "set_welcome"
            await q.edit_message_text(tx(lang,"write_welcome"),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(tx(lang,"b_clear"), callback_data="own_clear_welcome")],
                    *back(lang,"panel_unified")])); return

        if data == "own_clear_welcome":
            CFG["welcome_msg"] = ""; await save_cfg()
            q.data = "panel_unified"; await on_callback(update, ctx); return

        if data == "own_reset_stats":
            for k in ("total_dl","total_users"): CFG[k] = 0
            await save_cfg(); await q.answer(tx(lang,"own_reset_done"), show_alert=True); return

        if data == "own_backup":
            await q.answer(tx(lang,"own_backup_prep"), show_alert=False)
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

    if uid in waiting_state:
        state = waiting_state.pop(uid)

        if state == "set_welcome":
            CFG["welcome_msg"] = txt; await save_cfg()
            await msg.reply_text(tx(lang,"welcome_set")); return

        if state.startswith("broadcast_"):
            all_u = await all_uids(); ok = fail = 0
            st = await msg.reply_text(tx(lang,"broadcast_sending", total=len(all_u)))
            for i, t in enumerate(all_u):
                try:
                    await ctx.bot.copy_message(chat_id=t, from_chat_id=msg.chat_id, message_id=msg.message_id)
                    ok += 1; await asyncio.sleep(0.04)
                except: fail += 1
                if i % 100 == 0 and i > 0:
                    try: await st.edit_text(tx(lang,"broadcast_progress", done=i, total=len(all_u)))
                    except: pass
            await st.edit_text(tx(lang,"broadcast_done", ok=ok, fail=fail)); return

        if state.startswith("action_"):
            action = state[len("action_"):]

            if action == "add_ch":
                ch = txt.strip()
                if not ch.startswith("@") or len(ch) < 3:
                    await msg.reply_text(tx(lang,"act_ch_wrong_fmt")); return
                if ch not in channels_list:
                    channels_list.append(ch); await save_cfg()
                await msg.reply_text(tx(lang,"sup_ch_added", ch=ch)); return

            if not txt.strip().isdigit():
                await msg.reply_text(tx(lang,"invalid_id")); return
            tid = int(txt.strip())

            if action == "blk_add":
                blocked_set.add(tid); await save_cfg()
                await msg.reply_text(tx(lang,"act_blocked", id=tid))
            elif action == "info_check":
                ud = await user_get(tid)
                if not ud: await msg.reply_text(tx(lang,"user_not_found")); return
                await msg.reply_text(tx(lang,"userinfo_text",
                    name=ud.get("name","—"), user=ud.get("user","—"), id=tid,
                    vip=tx(lang,"vip_yes") if ud.get("vip") else tx(lang,"vip_no"),
                    lang=LANG_NAMES.get(ud.get("lang","—"),"—"),
                    dl=ud.get("dl",0), date=ud.get("date","—")))
            elif action == "adm_add":
                admins_set.add(tid); await save_cfg()
                await msg.reply_text(tx(lang,"act_adm_added", id=tid))
            elif action == "adm_rm":
                admins_set.discard(tid); await save_cfg()
                await msg.reply_text(tx(lang,"act_adm_removed", id=tid))
            elif action == "vip_add":
                vip_set.add(tid); await user_field(tid,"vip",True); await save_cfg()
                await msg.reply_text(tx(lang,"act_vip_added", id=tid))
            elif action == "vip_rm":
                vip_set.discard(tid); await user_field(tid,"vip",False); await save_cfg()
                await msg.reply_text(tx(lang,"act_vip_removed", id=tid))
            elif action == "sup_add":
                super_admins_set.add(tid); admins_set.add(tid); await save_cfg()
                await msg.reply_text(tx(lang,"act_sup_added", id=tid))
            return

    # ── Instagram Link ─────────────────────────────────────────────────────────
    if is_blocked(uid): return
    if CFG["maintenance"] and not is_admin(uid):
        await msg.reply_text(tx(lang,"maintenance_msg", dev=DEV)); return
    if not any(x in txt for x in ("instagram.com/reel", "instagram.com/p/")):
        return

    ok_sub, missing = await check_join(uid, ctx)
    if not ok_sub and not bypass_join(uid):
        kb = [[InlineKeyboardButton(f"📢 {ch}", url=f"https://t.me/{ch.lstrip('@')}")] for ch in missing]
        kb.append([InlineKeyboardButton(tx(lang,"b_joined"), callback_data="check_join_btn")])
        await msg.reply_text(tx(lang,"force_join"), reply_markup=InlineKeyboardMarkup(kb)); return

    async def animated_progress(status_msg):
        frames = ["⬜⬜⬜⬜⬜","⬛⬜⬜⬜⬜","⬛⬛⬜⬜⬜","⬛⬛⬛⬜⬜","⬛⬛⬛⬛⬜","⬛⬛⬛⬛⬛"]
        for frame in frames:
            try: await status_msg.edit_text(f"🔍 {frame}")
            except: pass
            await asyncio.sleep(0.4)

    status = await msg.reply_text("🔍 ⬜⬜⬜⬜⬜")
    progress_task = asyncio.create_task(animated_progress(status))

    try:
        insta_data = await fetch_instagram(txt)
        progress_task.cancel()
        if not insta_data:
            await status.edit_text(tx(lang,"invalid_link")); return

        await session_save(uid, insta_data)

        caption = tx(lang,"found",
            title=html.escape(clean_title(insta_data.get("title","Instagram Post"))),
            owner=html.escape(insta_data.get("owner","Instagram User")),
            views=fmt(insta_data.get("views",0)),
            likes=fmt(insta_data.get("likes",0)),
            comments=fmt(insta_data.get("comments",0)),
        )

        try: await status.delete()
        except: pass

        n_photos = len(insta_data.get("images",[]))
        kb = []
        if insta_data.get("video_url"):
            kb.append([InlineKeyboardButton(tx(lang,"b_video"), callback_data="dl_video")])
        if n_photos > 0:
            kb.append([InlineKeyboardButton(tx(lang,"b_photos",n=n_photos), callback_data="dl_photo")])
        if insta_data.get("audio_url"):
            kb.append([InlineKeyboardButton(tx(lang,"b_audio"), callback_data="dl_audio")])
        kb.append([InlineKeyboardButton(tx(lang,"b_delete"), callback_data="close")])

        await ctx.bot.send_message(uid, caption, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(kb))

    except Exception as e:
        progress_task.cancel()
        log.error(f"Instagram Error: {traceback.format_exc()}")
        try: await status.edit_text(tx(lang,"dl_fail"))
        except: pass

# ==============================================================================
# ── 7. FASTAPI WEBHOOK
# ==============================================================================
_token = TOKEN if TOKEN != "DUMMY_TOKEN" else "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
ptb = ApplicationBuilder().token(_token).build()
ptb.add_handler(CommandHandler(["start","menu"], cmd_start))
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
    d = "✅ Set" if DB_URL    else "❌ Missing"
    o = "✅ Set" if OWNER_ID  else "❌ Missing"
    html_content = f"""
    <html><head><title>InstaBot</title>
    <style>
        body{{font-family:Arial;background:#f4f4f9;padding:40px;direction:rtl;text-align:right}}
        .box{{background:#fff;padding:24px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,.1);max-width:560px;margin:0 auto}}
        li{{padding:10px 0;border-bottom:1px solid #eee;font-size:17px}}
    </style></head>
    <body><div class="box">
        <h2>📸 Instagram Bot — System Check</h2>
        <ul>
            <li>BOT_TOKEN: {t}</li>
            <li>DB_URL: {d}</li>
            <li>OWNER_ID: {o}</li>
        </ul>
        <p style="color:red">ئەگەر ❌ بوو، بڕۆ Vercel → Settings → Environment Variables</p>
    </div></body></html>
    """
    return HTMLResponse(content=html_content)
