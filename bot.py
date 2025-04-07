import os
import json
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from utils import load_users, save_users

TOKEN = os.getenv("BOT_TOKEN")

users = load_users()
searching = []
chat_pairs = {}

# Load fake users
with open("fake_users.json") as f:
    fake_users = json.load(f)

ads = [
    "📢 Try our premium version for more features!",
    "🔥 Follow us on Instagram for daily matches!",
    "💖 Sponsored: Meet people near you — now with location-based matching!"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    args = context.args

    if user_id not in users:
        users[user_id] = {"step": "name", "ref_by": args[0] if args else None}
        save_users(users)
        await update.message.reply_text("👋 Welcome! What's your name?")
    else:
        await update.message.reply_text("👋 Welcome back! Use /find to match.")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    msg = update.message.text

    if user_id in chat_pairs:
        partner_id = chat_pairs[user_id]
        if partner_id.startswith("fake"):
            await context.bot.send_message(user_id, "🤖 " + random.choice([
                "That's interesting!", "Haha really?", "Tell me more..."
            ]))
        else:
            await context.bot.send_message(int(partner_id), msg)
        return

    if user_id in users:
        step = users[user_id].get('step')
        users[user_id][step] = msg

        if step == 'name':
            users[user_id]['step'] = 'age'
            await update.message.reply_text("📅 How old are you?")
        elif step == 'age':
            users[user_id]['step'] = 'gender'
            await update.message.reply_text("🚻 Gender (Male/Female)?")
        elif step == 'gender':
            users[user_id]['step'] = 'bio'
            await update.message.reply_text("📝 Tell us about yourself:")
        elif step == 'bio':
            users[user_id]['step'] = 'done'
            await update.message.reply_text("✅ Profile saved! Click below to find a match:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❤️ Find Match", callback_data="find")]]))
        save_users(users)

async def find_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)

    if user_id in chat_pairs:
        await query.message.reply_text("⚠️ You're already in a chat. Type /stop to leave it.")
        return

    # Ad display
    if random.random() < 0.3:
        await query.message.reply_text(random.choice(ads))

    if len(searching) > 0:
        partner_id = searching.pop(0)
        chat_pairs[user_id] = partner_id
        chat_pairs[partner_id] = user_id
        await context.bot.send_message(int(partner_id), "❤️ Matched with someone!")
        await query.message.reply_text("❤️ Matched with someone!")
    else:
        fake = random.choice(fake_users)
        fake_id = fake['id']
        chat_pairs[user_id] = fake_id
        chat_pairs[fake_id] = user_id
        await context.bot.send_photo(chat_id=int(user_id), photo=fake['photo'])
        await context.bot.send_message(user_id, f"❤️ Matched with {fake['name']} ({fake['age']})\n📝 {fake['bio']}")
        await context.bot.send_message(user_id, random.choice(["Hi 😊", "Hey! How are you?", "Nice to meet you! "]))

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id in chat_pairs:
        partner_id = chat_pairs.pop(user_id)
        chat_pairs.pop(partner_id, None)
        if not partner_id.startswith("fake"):
            await context.bot.send_message(int(partner_id), "❌ The user left the chat.")
        await update.message.reply_text("👋 You left the chat.")
    else:
        await update.message.reply_text("❌ You're not in a chat.")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(CallbackQueryHandler(find_callback, pattern="find"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

print("🚀 Bot is running...")
app.run_polling()
