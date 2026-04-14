import asyncio
import json
import os
import base64
import logging
from datetime import datetime

import httpx
import rubpy

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ─── Config ───────────────────────────────────────────────────────────────────

TELEGRAM_BOT_TOKEN  = os.environ["TELEGRAM_BOT_TOKEN"]
RUBIKA_SESSION_B64  = os.environ.get("RUBIKA_SESSION_B64", "")
RUBIKA_TARGET_GUID  = os.environ["RUBIKA_TARGET_GUID"]  # GUID چتی که پیام‌ها ارسال میشن
CONFIG_FILE         = "config.json"
SESSION_FILE        = "rubika_session.json"
TELEGRAM_API        = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

# ─── Config helpers ───────────────────────────────────────────────────────────

def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"channels": [], "message_count": 5, "admin_chat_id": None}


def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    logger.info("Config saved.")


# ─── Session helpers ──────────────────────────────────────────────────────────

def restore_session():
    """Restore Rubika session from base64 env var."""
    if RUBIKA_SESSION_B64:
        try:
            data = base64.b64decode(RUBIKA_SESSION_B64).decode("utf-8")
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                f.write(data)
            logger.info("Rubika session restored from env.")
        except Exception as e:
            logger.warning(f"Could not restore session: {e}")


def export_session_b64() -> str:
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            return base64.b64encode(f.read().encode()).decode()
    return ""


# ─── Telegram helpers ─────────────────────────────────────────────────────────

async def tg_get(client: httpx.AsyncClient, method: str, **params) -> dict:
    r = await client.get(f"{TELEGRAM_API}/{method}", params=params, timeout=20)
    r.raise_for_status()
    return r.json()


async def tg_post(client: httpx.AsyncClient, method: str, **data) -> dict:
    r = await client.post(f"{TELEGRAM_API}/{method}", json=data, timeout=20)
    r.raise_for_status()
    return r.json()


async def get_last_messages(client: httpx.AsyncClient, channel: str, count: int) -> list[dict]:
    """
    دریافت آخرین پیام‌های کانال از طریق getUpdates.
    ربات باید ادمین چنل باشد و channel_post را دریافت کند.
    """
    messages = []
    try:
        resp = await tg_get(client, "getUpdates", limit=100, allowed_updates=["channel_post"])
        updates = resp.get("result", [])

        ch_clean = channel.lstrip("@").lower()

        for upd in updates:
            post = upd.get("channel_post", {})
            if not post:
                continue
            chat = post.get("chat", {})
            username = (chat.get("username") or "").lower()
            cid = str(chat.get("id", ""))

            if username == ch_clean or cid == channel:
                text = post.get("text") or post.get("caption") or "[media]"
                messages.append({
                    "text": text,
                    "date": post.get("date", 0),
                    "channel": channel,
                })

        messages = sorted(messages, key=lambda x: x["date"], reverse=True)[:count]
    except Exception as e:
        logger.error(f"Error fetching messages from {channel}: {e}")
    return messages


# ─── Rubika helper ────────────────────────────────────────────────────────────

async def send_to_rubika(messages: list[dict]):
    """Send messages to Rubika chat."""
    restore_session()
    try:
        async with rubpy.Client(session=SESSION_FILE) as app:
            for msg in messages:
                ch        = msg.get("channel", "")
                date_str  = datetime.fromtimestamp(msg.get("date", 0)).strftime("%Y-%m-%d %H:%M")
                text      = f"📢 کانال: {ch}\n🕐 {date_str}\n\n{msg['text']}"
                await app.send_message(RUBIKA_TARGET_GUID, text)
                await asyncio.sleep(1.5)  # جلوگیری از flood

        logger.info(f"Sent {len(messages)} messages to Rubika.")

        # اگر سشن تغییر کرد، لاگ کن تا بتوان Secret رو آپدیت کرد
        new_b64 = export_session_b64()
        if new_b64:
            logger.info(f"[SESSION_EXPORT] {new_b64}")

    except Exception as e:
        logger.error(f"Rubika send error: {e}")
        raise


# ─── Telegram admin panel ─────────────────────────────────────────────────────

async def handle_admin_updates(client: httpx.AsyncClient, cfg: dict, offset: int) -> int:
    """Process admin commands from Telegram bot."""
    resp    = await tg_get(client, "getUpdates", offset=offset, timeout=10, limit=50)
    updates = resp.get("result", [])

    for upd in updates:
        offset = upd["update_id"] + 1
        msg    = upd.get("message", {})
        if not msg:
            continue

        chat_id = msg["chat"]["id"]
        text    = msg.get("text", "").strip()

        # ثبت ادمین اولین بار
        if cfg.get("admin_chat_id") is None:
            cfg["admin_chat_id"] = chat_id
            save_config(cfg)
            await tg_post(client, "sendMessage",
                          chat_id=chat_id,
                          text="✅ شما به عنوان ادمین ثبت شدید!")

        if chat_id != cfg.get("admin_chat_id"):
            await tg_post(client, "sendMessage",
                          chat_id=chat_id, text="⛔ دسترسی ندارید.")
            continue

        # ─── Commands ─────────────────────────────────────────────────────────

        if text in ("/start", "/help"):
            help_text = (
                "🤖 *ربات مدیریت خبرخوان*\n\n"
                "دستورات:\n"
                "/channels – لیست کانال‌های فعال\n"
                "/add @channel – اضافه کردن کانال\n"
                "/remove @channel – حذف کانال\n"
                "/count N – تعداد پیام (مثلاً /count 5)\n"
                "/status – وضعیت فعلی\n"
                "/run – اجرای دستی\n"
            )
            await tg_post(client, "sendMessage",
                          chat_id=chat_id, text=help_text, parse_mode="Markdown")

        elif text == "/channels":
            chs   = cfg.get("channels", [])
            reply = ("📋 کانال‌های فعال:\n" + "\n".join(f"• {c}" for c in chs)
                     if chs else "❌ هیچ کانالی اضافه نشده.")
            await tg_post(client, "sendMessage", chat_id=chat_id, text=reply)

        elif text.startswith("/add "):
            ch = text[5:].strip()
            if not ch:
                await tg_post(client, "sendMessage", chat_id=chat_id,
                              text="❌ نام کانال را وارد کنید. مثال: /add @channelname")
            elif ch in cfg["channels"]:
                await tg_post(client, "sendMessage", chat_id=chat_id,
                              text="⚠️ این کانال قبلاً اضافه شده.")
            else:
                cfg["channels"].append(ch)
                save_config(cfg)
                await tg_post(client, "sendMessage", chat_id=chat_id,
                              text=f"✅ کانال {ch} اضافه شد.")

        elif text.startswith("/remove "):
            ch = text[8:].strip()
            if ch in cfg["channels"]:
                cfg["channels"].remove(ch)
                save_config(cfg)
                await tg_post(client, "sendMessage", chat_id=chat_id,
                              text=f"🗑 کانال {ch} حذف شد.")
            else:
                await tg_post(client, "sendMessage", chat_id=chat_id,
                              text="❌ این کانال در لیست نیست.")

        elif text.startswith("/count "):
            try:
                n = int(text[7:].strip())
                if 1 <= n <= 20:
                    cfg["message_count"] = n
                    save_config(cfg)
                    await tg_post(client, "sendMessage", chat_id=chat_id,
                                  text=f"✅ تعداد پیام به {n} تغییر کرد.")
                else:
                    await tg_post(client, "sendMessage", chat_id=chat_id,
                                  text="❌ عدد باید بین 1 تا 20 باشد.")
            except ValueError:
                await tg_post(client, "sendMessage", chat_id=chat_id,
                              text="❌ عدد صحیح وارد کنید. مثال: /count 5")

        elif text == "/status":
            chs    = cfg.get("channels", [])
            count  = cfg.get("message_count", 5)
            status = (
                f"📊 *وضعیت ربات*\n\n"
                f"کانال‌ها: {len(chs)}\n"
                f"تعداد پیام هر دوره: {count}\n"
                f"زمان اجرا: هر ۱ ساعت\n"
            )
            await tg_post(client, "sendMessage",
                          chat_id=chat_id, text=status, parse_mode="Markdown")

        elif text == "/run":
            await tg_post(client, "sendMessage", chat_id=chat_id,
                          text="▶️ در حال اجرای دستی...")
            await run_news_fetch(client, cfg)
            await tg_post(client, "sendMessage", chat_id=chat_id,
                          text="✅ اجرا تمام شد.")

        else:
            await tg_post(client, "sendMessage", chat_id=chat_id,
                          text="❓ دستور ناشناخته. /help بزنید.")

    return offset


# ─── Main news fetch logic ────────────────────────────────────────────────────

async def run_news_fetch(client: httpx.AsyncClient, cfg: dict):
    channels = cfg.get("channels", [])
    count    = cfg.get("message_count", 5)

    if not channels:
        logger.warning("No channels configured.")
        return

    all_messages = []
    for ch in channels:
        msgs = await get_last_messages(client, ch, count)
        all_messages.extend(msgs)
        logger.info(f"Fetched {len(msgs)} messages from {ch}")

    if all_messages:
        await send_to_rubika(all_messages)
    else:
        logger.info("No new messages to send.")


# ─── Entry point ──────────────────────────────────────────────────────────────

async def main():
    cfg = load_config()

    async with httpx.AsyncClient() as client:
        logger.info("Processing admin commands...")
        await handle_admin_updates(client, cfg, offset=0)

        logger.info("Running news fetch...")
        await run_news_fetch(client, cfg)

    logger.info("All done.")


if __name__ == "__main__":
    asyncio.run(main())
