from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import random

users = {}  # user_id: {name, age, gender, bio}
searching = []
chat_pairs = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text("Welcome to Dating Bot! What's your name?")
    users[user_id] = {'step': 'name'}

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
            await update.message.reply_text("How old are you?")
        elif step == 'age':
            users[user_id]['age'] = msg
            users[user_id]['step'] = 'gender'
            await update.message.reply_text("Your gender? (Male/Female)")
        elif step == 'gender':
            users[user_id]['gender'] = msg
            users[user_id]['step'] = 'bio'
            await update.message.reply_text("Write a short bio about yourself:")
        elif step == 'bio':
            users[user_id]['bio'] = msg
            users[user_id]['step'] = 'done'
            await update.message.reply_text("✅ Registration complete! Type /find to meet someone.")
        else:
            await update.message.reply_text("Type /find to meet someone.")

async def find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in chat_pairs:
        await update.message.reply_text("You're already chatting. Type /stop to end.")
        return

    if user_id in searching:
        await update.message.reply_text("Already searching...")
        return

    if len(searching) > 0:
        partner_id = searching.pop(0)
        chat_pairs[user_id] = partner_id
        chat_pairs[partner_id] = user_id
        await context.bot.send_message(user_id, "❤️ Matched! Say hi!")
        await context.bot.send_message(partner_id, "❤️ Matched! Say hi!")
    else:
        searching.append(user_id)
        await update.message.reply_text("🔍 Searching for a match... Please wait.")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in chat_pairs:
        partner_id = chat_pairs.pop(user_id)
        chat_pairs.pop(partner_id, None)
        await context.bot.send_message(partner_id, "❌ The chat was ended.")
        await update.message.reply_text("You left the chat.")
    else:
        await update.message.reply_text("You're not in a chat.")

app = ApplicationBuilder().token("YOUR_BOT_TOKEN_HERE").build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("find", find))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

print("Bot is running...")
app.run_polling()
