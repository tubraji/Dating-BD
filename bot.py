import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Bot token will be taken from Environment Variable
TOKEN = os.getenv("BOT_TOKEN")

# Store registered users
users = {}
searching = []
chat_pairs = {}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("👋 Welcome to the Dating Bot!\nWhat's your name?")
    users[user_id] = {'step': 'name'}

# Handle user registration and chat
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message.text

    if user_id in chat_pairs:
        partner_id = chat_pairs[user_id]
        await context.bot.send_message(partner_id, f"💌: {msg}")
        return

    if user_id in users:
        step = users[user_id].get('step')
        if step == 'name':
            users[user_id]['name'] = msg
            users[user_id]['step'] = 'age'
            await update.message.reply_text("📅 How old are you?")
        elif step == 'age':
            users[user_id]['age'] = msg
            users[user_id]['step'] = 'gender'
            await update.message.reply_text("🚻 Your gender? (Male/Female)")
        elif step == 'gender':
            users[user_id]['gender'] = msg
            users[user_id]['step'] = 'bio'
            await update.message.reply_text("📝 Write a short bio:")
        elif step == 'bio':
            users[user_id]['bio'] = msg
            users[user_id]['step'] = 'done'
            await update.message.reply_text("✅ Registration complete! Type /find to meet someone new!")
        else:
            await update.message.reply_text("🔍 Type /find to search for someone to chat.")

# Find command
async def find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in chat_pairs:
        await update.message.reply_text("⚠️ You are already in a chat! Type /stop to end it.")
        return

    if user_id in searching:
        await update.message.reply_text("⏳ Still searching... please wait.")
        return

    if len(searching) > 0:
        partner_id = searching.pop(0)
        chat_pairs[user_id] = partner_id
        chat_pairs[partner_id] = user_id
        await context.bot.send_message(user_id, "❤️ Matched! Say hi!")
        await context.bot.send_message(partner_id, "❤️ Matched! Say hi!")
    else:
        searching.append(user_id)
        await update.message.reply_text("🔎 Searching for a match... Please wait.")

# Stop command
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in chat_pairs:
        partner_id = chat_pairs.pop(user_id)
        chat_pairs.pop(partner_id, None)
        await context.bot.send_message(partner_id, "❌ The chat has ended.")
        await update.message.reply_text("👋 You have left the chat.")
    else:
        await update.message.reply_text("⚠️ You're not in a chat right now.")

# Main setup
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("find", find))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

print("🚀 Bot is running...")
app.run_polling()
