import os
import json
import random
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ChatActions
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "@deletedonf")

if not API_TOKEN:
    raise ValueError("⚠️ BOT_TOKEN is missing in environment variables!")

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Load or initialize users
try:
    with open("users.json", "r") as f:
        users = json.load(f)
except:
    users = {}

# Load or initialize ads
try:
    with open("ads.json", "r") as f:
        ads = json.load(f)
except:
    ads = []

# === Add Fake Users if none exist ===
FAKE_USER_COUNT = 25
if not users:
    fake_names = ["Tania", "Mimi", "Sadia", "Nusrat", "Lamia", "Farzana", "Tumpa", "Faria", "Rita", "Sinthia",
                  "Samiha", "Nusrat", "Mehzabin", "Oni", "Shanta", "Shorna", "Sadia", "Riya", "Nishi", "Mahi",
                  "Ruma", "Poly", "Toma", "Sonia", "Ayesha"]
    for i in range(FAKE_USER_COUNT):
        user_id = f"fake_{i+1}"
        users[user_id] = {
            "name": fake_names[i % len(fake_names)],
            "age": str(random.randint(18, 30)),
            "gender": "Female",
            "bio": "Just looking to chat ❤️",
            "partner": None
        }
    with open("users.json", "w") as f:
        json.dump(users, f)

# Registration States
class Register(StatesGroup):
    name = State()
    age = State()
    gender = State()
    bio = State()

# Helper Buttons
def get_chat_buttons():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("Next", callback_data="next"),
        InlineKeyboardButton("Stop", callback_data="stop")
    )
    return kb

def get_random_ad():
    return random.choice(ads) if ads else None

def is_admin(username):
    return username == ADMIN_USERNAME

def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f)

def save_ads():
    with open("ads.json", "w") as f:
        json.dump(ads, f)

# Start Command
@dp.message_handler(commands=['start'])
async def start_cmd(msg: types.Message, state: FSMContext):
    user_id = str(msg.from_user.id)
    args = msg.get_args()
    if user_id not in users:
        users[user_id] = {
            "name": "",
            "age": "",
            "gender": "",
            "bio": "",
            "partner": None,
            "referred_by": args if args else None
        }
        save_users()
        await msg.answer("👋 Welcome! Let's get you registered.")
        await msg.answer("What's your name?")
        await Register.name.set()
    else:
        await msg.answer("You're already registered. Use /find to chat.")

@dp.message_handler(state=Register.name)
async def reg_name(msg: types.Message, state: FSMContext):
    users[str(msg.from_user.id)]["name"] = msg.text
    await msg.answer("Your age?")
    await Register.next()

@dp.message_handler(state=Register.age)
async def reg_age(msg: types.Message, state: FSMContext):
    users[str(msg.from_user.id)]["age"] = msg.text
    await msg.answer("Your gender?")
    await Register.next()

@dp.message_handler(state=Register.gender)
async def reg_gender(msg: types.Message, state: FSMContext):
    users[str(msg.from_user.id)]["gender"] = msg.text
    await msg.answer("Write a short bio")
    await Register.next()

@dp.message_handler(state=Register.bio)
async def reg_bio(msg: types.Message, state: FSMContext):
    users[str(msg.from_user.id)]["bio"] = msg.text
    save_users()
    await msg.answer("✅ Registration complete! Use /find to connect with someone.")
    await state.finish()

# Admin Commands
@dp.message_handler(commands=["addad"])
async def add_ad(msg: types.Message):
    if is_admin(msg.from_user.username):
        ad = msg.get_args()
        if ad:
            ads.append(ad)
            save_ads()
            await msg.reply("✅ Ad added.")
        else:
            await msg.reply("Usage: /addad <text>")

@dp.message_handler(commands=["ads"])
async def list_ads(msg: types.Message):
    if is_admin(msg.from_user.username):
        if ads:
            await msg.reply("\n".join([f"{i+1}. {ad}" for i, ad in enumerate(ads)]))
        else:
            await msg.reply("No ads added yet.")

@dp.message_handler(commands=["delad"])
async def del_ad(msg: types.Message):
    if is_admin(msg.from_user.username):
        try:
            index = int(msg.get_args()) - 1
            ads.pop(index)
            save_ads()
            await msg.reply("✅ Ad deleted.")
        except:
            await msg.reply("❌ Invalid index. Use /ads to check list.")

@dp.message_handler(commands=["broadcast"])
async def broadcast(msg: types.Message):
    if is_admin(msg.from_user.username):
        text = msg.get_args()
        count = 0
        for uid in users:
            try:
                await bot.send_message(uid, text)
                count += 1
            except:
                pass
        await msg.reply(f"✅ Broadcast sent to {count} users.")

@dp.message_handler(commands=["find"])
async def find_partner(msg: types.Message):
    user_id = str(msg.from_user.id)
    if users[user_id].get("partner"):
        await msg.answer("You're already in a chat.")
        return
    for uid, data in users.items():
        if uid != user_id and not data.get("partner"):
            users[user_id]["partner"] = uid
            users[uid]["partner"] = user_id
            save_users()
            await bot.send_message(uid, "🔗 You're connected!", reply_markup=get_chat_buttons())
            await bot.send_message(user_id, "🔗 You're connected!", reply_markup=get_chat_buttons())
            return
    await msg.answer("❌ No one available. Try again soon.")

@dp.callback_query_handler(lambda c: c.data in ["next", "stop"])
async def handle_buttons(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    partner_id = users[user_id].get("partner")
    if partner_id:
        users[user_id]["partner"] = None
        users[partner_id]["partner"] = None
        save_users()
        await bot.send_message(partner_id, "❌ Partner left the chat.")
        await callback.message.answer("🔄 Use /find to chat with someone new.")
    else:
        await callback.message.answer("You're not in a chat. Use /find")
    await callback.answer()

@dp.message_handler()
async def chat_handler(msg: types.Message):
    user_id = str(msg.from_user.id)
    partner_id = users.get(user_id, {}).get("partner")
    if partner_id:
        await bot.send_chat_action(partner_id, ChatActions.TYPING)
        await bot.send_message(partner_id, msg.text, reply_markup=get_chat_buttons())
        ad = get_random_ad()
        if ad:
            await bot.send_message(user_id, f"\n💬 Sponsored: {ad}")
    else:
        await msg.reply("❌ You're not in a chat. Use /find")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
