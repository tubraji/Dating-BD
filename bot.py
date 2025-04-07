import json
import random
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ChatActions
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = 'YOUR_BOT_TOKEN_HERE'
ADMIN_USERNAME = '@deletedonf'

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# Load or initialize users
try:
    with open('users.json', 'r') as f:
        users = json.load(f)
except:
    users = {}

# Load or initialize ads
try:
    with open('ads.json', 'r') as f:
        ads = json.load(f)
except:
    ads = []

# States
class Register(StatesGroup):
    name = State()
    age = State()
    gender = State()
    bio = State()

# Inline Buttons
def get_chat_buttons():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("Next", callback_data="next"),
        InlineKeyboardButton("Stop", callback_data="stop")
    )
    return kb

# Ads
def get_random_ad():
    return random.choice(ads) if ads else None

# Admin Check
def is_admin(username):
    return username == ADMIN_USERNAME

# Save users
def save_users():
    with open('users.json', 'w') as f:
        json.dump(users, f)

# Save ads
def save_ads():
    with open('ads.json', 'w') as f:
        json.dump(ads, f)

# Commands
@dp.message_handler(commands=['start'])
async def start_cmd(msg: types.Message):
    args = msg.get_args()
    user_id = str(msg.from_user.id)
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
        await msg.answer("Welcome! Let's register you.")
        await msg.answer("What's your name?")
        await Register.name.set()
    else:
        await msg.answer("You're already registered. Use /find to start chatting.")

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
    await msg.answer("Write a short bio.")
    await Register.next()

@dp.message_handler(state=Register.bio)
async def reg_bio(msg: types.Message, state: FSMContext):
    users[str(msg.from_user.id)]["bio"] = msg.text
    save_users()
    await msg.answer("✅ Registration complete! Use /find to start chatting.")
    await state.finish()

# Admin Commands
@dp.message_handler(commands=['addad'])
async def add_ad(msg: types.Message):
    if is_admin(msg.from_user.username):
        text = msg.get_args()
        if text:
            ads.append(text)
            save_ads()
            await msg.reply("✅ Ad added.")
        else:
            await msg.reply("Usage: /addad your ad text")

@dp.message_handler(commands=['ads'])
async def list_ads(msg: types.Message):
    if is_admin(msg.from_user.username):
        if ads:
            await msg.reply("\n".join([f"{i+1}. {ad}" for i, ad in enumerate(ads)]))
        else:
            await msg.reply("No ads available.")

@dp.message_handler(commands=['delad'])
async def del_ad(msg: types.Message):
    if is_admin(msg.from_user.username):
        try:
            index = int(msg.get_args()) - 1
            ads.pop(index)
            save_ads()
            await msg.reply("✅ Ad deleted.")
        except:
            await msg.reply("Invalid index. Use /ads to see list.")

@dp.message_handler(commands=['broadcast'])
async def broadcast(msg: types.Message):
    if is_admin(msg.from_user.username):
        text = msg.get_args()
        if text:
            for uid in users:
                try:
                    await bot.send_message(uid, text)
                except:
                    pass
            await msg.reply("✅ Broadcast sent.")

@dp.message_handler(commands=['find'])
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
    await msg.answer("❌ No one is available now. Try again later.")

@dp.callback_query_handler(lambda c: c.data in ["next", "stop"])
async def handle_buttons(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    partner_id = users[user_id].get("partner")
    if partner_id:
        users[user_id]["partner"] = None
        users[partner_id]["partner"] = None
        save_users()
        await bot.send_message(partner_id, "❌ Partner left the chat.")
        await callback.message.answer("🔄 Searching new partner... Use /find")
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
        await msg.reply("❌ You are not connected. Use /find")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
