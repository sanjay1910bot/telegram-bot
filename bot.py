import os
import time
import requests
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8623865225:AAG2GoTyodz36wBgY7AET_CDo2eTa1x3rV8"

# Anti-spam
user_time = {}

def allowed(user_id):
    now = time.time()
    if user_id in user_time and now - user_time[user_id] < 8:
        return False
    user_time[user_id] = now
    return True

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 PRO+ Downloader Bot\n\n"
        "Send any link:\n"
        "• YouTube 🎥\n"
        "• Instagram 📸\n"
        "• Files 📁"
    )

# AUTO DETECT
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.id
    text = update.message.text

    print(f"{user}: {text}")

    if not allowed(user):
        await update.message.reply_text("⏳ Wait a few seconds...")
        return

    if "youtube.com" in text or "youtu.be" in text:
        kb = [
            [InlineKeyboardButton("360p", callback_data=f"360|{text}")],
            [InlineKeyboardButton("720p", callback_data=f"720|{text}")],
            [InlineKeyboardButton("1080p", callback_data=f"1080|{text}")],
            [InlineKeyboardButton("Best HD+", callback_data=f"best|{text}")],
            [InlineKeyboardButton("MP3", callback_data=f"mp3|{text}")]
        ]
        await update.message.reply_text("🎥 Choose quality:", reply_markup=InlineKeyboardMarkup(kb))

    elif "instagram.com" in text:
        msg = await update.message.reply_text("📸 Downloading...")
        await download_video(update, text, "best", msg)

    elif text.startswith("http"):
        msg = await update.message.reply_text("📁 Downloading...")
        await download_file(update, text, msg)

# BUTTON
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    action, url = q.data.split("|")
    msg = await q.edit_message_text("⏳ Processing...")

    if action == "360":
        await download_video(q, url, "worst", msg)
    elif action == "720":
        await download_video(q, url, "best[height<=720]", msg)
    elif action == "1080":
        await download_video(q, url, "bestvideo[height<=1080]+bestaudio", msg)
    elif action == "best":
        await download_video(q, url, "bestvideo+bestaudio", msg)
    elif action == "mp3":
        await download_audio(q, url, msg)

# VIDEO
async def download_video(ctx, url, quality, msg):
    try:
        ydl_opts = {
            "format": quality,
            "outtmpl": "%(title)s.%(ext)s",
            "merge_output_format": "mp4"
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file = ydl.prepare_filename(info)

        size = os.path.getsize(file) / (1024 * 1024)

        if size > 50:
            await msg.edit_text(f"⚠️ Large file ({round(size,1)}MB)\nOpen link:\n{url}")
            os.remove(file)
            return

        await msg.edit_text("📤 Uploading...")
        await ctx.message.reply_video(open(file, "rb"))
        os.remove(file)

    except Exception as e:
        await ctx.message.reply_text(f"❌ Error: {e}")

# AUDIO
async def download_audio(ctx, url, msg):
    try:
        ydl_opts = {
            "format": "bestaudio",
            "outtmpl": "%(title)s.%(ext)s",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3"
            }]
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file = ydl.prepare_filename(info).replace(".webm", ".mp3")

        await msg.edit_text("🎧 Uploading...")
        await ctx.message.reply_audio(open(file, "rb"))
        os.remove(file)

    except Exception as e:
        await ctx.message.reply_text(f"❌ Error: {e}")

# FILE
async def download_file(update, url, msg):
    try:
        r = requests.get(url, stream=True)
        size = int(r.headers.get('content-length', 0)) / (1024*1024)

        if size > 50:
            await msg.edit_text("⚠️ File too large\nOpen link:\n" + url)
            return

        name = url.split("/")[-1] or "file"

        with open(name, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)

        await msg.edit_text("📤 Uploading...")
        await update.message.reply_document(open(name, "rb"))
        os.remove(name)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

# MAIN
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
app.add_handler(CallbackQueryHandler(button))

print("🔥 PRO+ Bot Running...")
app.run_polling()
