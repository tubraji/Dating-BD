import os
import datetime
import random
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# Bot token from environment variable
TOKEN = os.getenv("BOT_TOKEN")

# User & chat storage
users = {}
searching = []
chat_pairs = {}

# Fake users with image
fake_users = [
    {
        "id": -1001, "name": "Sadia", "age": "22", "gender": "Female", 
        "bio": "I love books and coffee ☕", 
        "photo": "https://i.imgur.com/9n0ZPzL.jpg"
    },
    {
        "id": -1002, "name": "Rafi", "age": "24", "gender": "Male", 
        "bio": "Gym freak 💪", 
        "photo": "https://i.imgur.com/VO3gG0R.jpg"
    },
    {
        "id": -1003, "name": "Tania", "age": "20", "gender": "Female", 
        "bio": "Netflix is my thing 🎬", 
        "photo": "https://i.imgur.com/nz8klFX.jpg"
    },
]

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users[user_id] = {'step': 'name'}
    await update.message.reply_text("👋 Welcome to the Dating Bot!\nWhat's your name?")

# Handle messages (registration + chat)
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    msg = update.message.text

    if user_id in chat_pairs:
        partner_id = chat_pairs[user_id]

        # Save log
        with open("chat_logs.txt", "a") as f:
            f.write(f"[{datetime.datetime.now()}] {user_id} ➡ {partner_id} : {msg}\n")

        # Fake user auto-reply
        if partner_id < 0:
            reply = random.choice([
                "Oh that's cool!",
                "Really? I like that too!",
                "Haha you're funny!",
                "Hmm... tell me more!"
            ])
            await context.bot.send_message(user_id, f"🤖 {reply}")
        else:
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
            users[user_id]['step'] = 'photo'
            await update.message.reply_text("📸 Send your profile photo:")
        elif step == 'photo':
            await update.message.reply_text("⚠️ Please send a photo, not text.")
        elif step == 'done':
            await update.message.reply_text("✅ You're registered! Type /find to meet someone new.")

# Handle photo as profile picture
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in users and users[user_id].get('step') == 'photo':
        photo_file = update.message.photo[-1].file_id
        users[user_id]['photo'] = photo_file
        users[user_id]['step'] = 'done'
        await update.message.reply_text("✅ Profile created! Type /find to meet someone!")
    elif user_id in chat_pairs:
        # In chat: forward photo
        partner_id = chat_pairs[user_id]
        photo = update.message.photo[-1].file_id
        await context.bot.send_photo(partner_id, photo=photo)

# Handle video sharing
async def video_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in chat_pairs:
        partner_id = chat_pairs[user_id]
        await context.bot.send_video(partner_id, video=update.message.video.file_id)

# Match command
async def find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in chat_pairs:
        await update.message.reply_text("⚠️ You're already in a chat. Type /stop to leave.")
        return

    if user_id in searching:
        await update.message.reply_text("⏳ Searching... Please wait.")
        return

    if len(searching) > 0:
        partner_id = searching.pop(0)
        chat_pairs[user_id] = partner_id
        chat_pairs[partner_id] = user_id
        await context.bot.send_message(user_id, "❤️ Matched! Say hi!")
        await context.bot.send_message(partner_id, "❤️ Matched! Say hi!")
    else:
        # No real user? Pick fake
        fake = random.choice(fake_users)
        fake_id = fake["id"]

        chat_pairs[user_id] = fake_id
        chat_pairs[fake_id] = user_id

        await context.bot.send_photo(user_id, photo=fake["photo"])
        await context.bot.send_message(user_id, f"❤️ Matched with {fake['name']}!\n📅 Age: {fake['age']}\n📝 Bio: {fake['bio']}")
        await context.bot.send_message(user_id, "💬 " + random.choice([
            "Hi there! 😊",
            "You look interesting 😍",
            "Tell me something about you!",
            "What do you do?"
        ]))

# Leave chat
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in chat_pairs:
        partner_id = chat_pairs.pop(user_id)
        chat_pairs.pop(partner_id, None)
        if partner_id > 0:
            await context.bot.send_message(partner_id, "❌ The chat has ended.")
        await update.message.reply_text("👋 You have left the chat.")
    else:
        await update.message.reply_text("⚠️ You're not in a chat.")

# Bot setup
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("find", find))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
app.add_handler(MessageHandler(filters.VIDEO, video_handler))

print("🚀 Bot is running...")
app.run_polling()
