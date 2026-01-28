import os
import json
import random
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

# ============ সেটিংস ============
BOT_TOKEN = os.getenv("BOT_TOKEN", "8006015641:AAHMiqhkmtvRmdLMN1Rbz2EnwsIrsGfH8qU")
ADMIN_ID = int(os.getenv("ADMIN_ID", "1858324638"))
VIDEO_CHANNEL_ID = int(os.getenv("VIDEO_CHANNEL_ID", "-1003872857468"))
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@CineflixOfficialbd")

# লগিং
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

print("🤖 Cineflix Bot Starting...")

# ============ ডাটাবেজ ============
class Database:
    def __init__(self):
        self.file = "data.json"
        self.load()
    
    def load(self):
        try:
            with open(self.file, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except:
            self.data = {"videos": {}}
    
    def save(self):
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def add_video(self, message_id, caption=""):
        code = f"v_{random.randint(100000, 999999)}"
        self.data["videos"][code] = {
            "message_id": message_id,
            "title": caption[:100] if caption else "Video",
            "date": datetime.now().strftime("%d-%m-%Y %H:%M")
        }
        self.save()
        return code
    
    def get_video(self, code):
        return self.data["videos"].get(code)

db = Database()

# ============ হেল্পার ফাংশন ============
async def check_member(user_id, bot):
    try:
        member = await bot.get_chat_member(VIDEO_CHANNEL_ID, user_id)
        return member.status in ["creator", "administrator", "member"]
    except:
        return False

# ============ কমান্ড ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if context.args:
        code = context.args[0]
        await handle_code(update, context, code)
        return
    
    await update.message.reply_text(
        f"🎬 Cineflix Bot\n\n"
        f"Send video code: v_123456\n\n"
        f"Channel: {CHANNEL_USERNAME}",
        parse_mode="Markdown"
    )

async def handle_code(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str):
    user = update.effective_user
    
    if not await check_member(user.id, context.bot):
        keyboard = [
            [InlineKeyboardButton("✅ Join Channel", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")],
            [InlineKeyboardButton("🔍 Check", callback_data=f"check_{code}")]
        ]
        await update.message.reply_text(
            f"Join {CHANNEL_USERNAME} first!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    await send_video(update, context, code, user.id)

async def send_video(update: Update, context: ContextTypes.DEFAULT_TYPE, code: str, user_id: int):
    if not code.startswith("v_"):
        await update.message.reply_text("❌ Invalid code!")
        return
    
    video = db.get_video(code)
    if not video:
        await update.message.reply_text("❌ Video not found!")
        return
    
    try:
        await context.bot.copy_message(
            chat_id=user_id,
            from_chat_id=VIDEO_CHANNEL_ID,
            message_id=video["message_id"],
            caption=f"🎬 {video['title']}\n✅ @Cinaflix_Streembot"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")

# ============ ক্যালব্যাক ============
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("check_"):
        code = query.data.replace("check_", "")
        user_id = query.from_user.id
        
        if await check_member(user_id, context.bot):
            await query.edit_message_text("✅ Sending...")
            await send_video(update, context, code, user_id)
        else:
            await query.answer("❌ Not joined!", show_alert=True)

# ============ চ্যানেল ============
async def channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post
    if msg and (msg.video or msg.document):
        code = db.add_video(msg.message_id, msg.caption)
        print(f"New video: {code}")

# ============ মেইন ============
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.ChatType.CHANNEL, channel_handler))
    
    async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        if text and (text.startswith("v_") or text.startswith("d_")):
            await handle_code(update, context, text)
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    print("✅ Bot is running!")
    app.run_polling()

if __name__ == "__main__":
    main()
