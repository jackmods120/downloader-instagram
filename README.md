# 📸 Instagram Downloader Telegram Bot

بۆتی تیلیگرام بۆ داگرتنی ڤیدیۆ و ریلزی ئینستاگرام.

## پێویستەکان

| Variable | پێویستە؟ | تێبینی |
|---|---|---|
| `BOT_TOKEN` | ✅ بەڵێ | لە @BotFather وەربگرە |
| `OWNER_ID` | ✅ بەڵێ | ئایدیی تیلیگرامت |
| `DB_URL` | ❌ ئارەزووی | Firebase — بۆ خەزنکردنی داتا |
| `DB_SECRET` | ❌ ئارەزووی | Firebase secret |
| `DEV_USERNAME` | ❌ ئارەزووی | یوزەرنەیمت بۆ پەیوەندی |
| `CHANNEL_URL` | ❌ ئارەزووی | لینکی چەناڵەکەت |

## Deploy بکە

1. لە Vercel، Environment Variables زیاد بکە
2. Deploy بکە
3. Webhook دامەزرێنە:
```
https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://your-site.vercel.app/api/main
```

## API Endpoints

- `GET /api/main` — Health check
- `POST /api/main` — Telegram webhook
- `GET /api/video?postUrl=...` — ڕاستەوخۆ ڤیدیۆ وەربگرە
