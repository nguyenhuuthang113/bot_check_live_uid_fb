import requests
import json
import asyncio
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "uids.json"

# ===== LOAD DATA =====
try:
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
except:
    data = {}

def save():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ===== CHECK UID =====
def check_uid(uid):
    try:
        url = f"https://graph.facebook.com/{uid}/picture?type=normal"
        r = requests.get(url, allow_redirects=True, timeout=10)
        final_url = r.url

        if "scontent" in final_url:
            return "LIVE"
        else:
            return "DIE"
    except:
        return "ERROR"

# ===== COMMANDS =====

chat_ids = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_ids.add(update.effective_chat.id)
    await update.message.reply_text("✅ Bot đang chạy!")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Dùng: /add UID")
        return

    uid = context.args[0]

    status = check_uid(uid)
    data[uid] = status
    save()

    await update.message.reply_text(f"{uid} hiện tại: {status}")

async def list_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not data:
        await update.message.reply_text("Chưa có UID")
        return

    msg = "\n".join([f"{uid} => {st}" for uid, st in data.items()])
    await update.message.reply_text(msg)

async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return

    uid = context.args[0]

    if uid in data:
        del data[uid]
        save()
        await update.message.reply_text(f"Đã xóa {uid}")
    else:
        await update.message.reply_text("UID không tồn tại")

# ===== BACKGROUND CHECK =====

async def checker(app):
    await asyncio.sleep(10)  # đợi bot start xong

    while True:
        for uid in list(data.keys()):
            try:
                old = data.get(uid)
                new = check_uid(uid)

                if new == "ERROR":
                    continue

                if old != new:
                    for chat_id in chat_ids:
                        await app.bot.send_message(
                            chat_id=chat_id,
                            text=f"🔔 {uid}: {old} → {new}"
                        )

                    data[uid] = new
                    save()

            except:
                pass

        await asyncio.sleep(60)  # check mỗi 60s

# ===== MAIN =====

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_uid))
    app.add_handler(CommandHandler("remove", remove))

    asyncio.create_task(checker(app))

    print("Bot started...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
