# import json
# import sqlite3
# import random
# import asyncio
# from aiogram import Bot, Dispatcher, types, F
# from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
# from aiogram.enums import ParseMode
# from aiogram.utils.keyboard import InlineKeyboardBuilder
# from aiogram.filters import Command
# from aiogram.client.default import DefaultBotProperties
# from aiogram.fsm.storage.memory import MemoryStorage
# from aiogram.fsm.context import FSMContext
# from aiogram.fsm.state import State, StatesGroup

# API_TOKEN = "7953097750:AAFigo9U_h89oCuHt1jHXDZkEv_fcLzme3Q"


import json
import sqlite3
import random
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

API_TOKEN = "7953097750:AAFigo9U_h89oCuHt1jHXDZkEv_fcLzme3Q"
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

WORDS_FILE = "in.json"
MNEMONIC_FILE = "mnemo.json"
WORDS_PER_DAY = 10  # 100 ta so‘z bo‘lsa, 10 kunda tugaydi

class LearningState(StatesGroup):
    selecting_day = State()
    learning_words = State()
    testing_words = State()

@dp.message(Command("start"))
async def start_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Assalomu alaykum!\n\nBugun qaysi <b>kunlik</b> darsni boshlaymiz?",
        reply_markup=generate_day_buttons()
    )
    await state.set_state(LearningState.selecting_day)

def generate_day_buttons():
    builder = InlineKeyboardBuilder()
    for i in range(1, 11):  # faqat 10 kun
        builder.button(text=str(i), callback_data=f"day_{i}")
    builder.adjust(5)
    return builder.as_markup()

def load_words(day: int):
    with open(WORDS_FILE, "r", encoding="utf-8") as f:
        words = json.load(f)
    start = (day - 1) * WORDS_PER_DAY
    day_words = words[start:start + WORDS_PER_DAY]
    random.shuffle(day_words)
    return day_words

def load_mnemonics():
    try:
        with open(MNEMONIC_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

@dp.callback_query(F.data.startswith("day_"))
async def handle_day_selection(callback: types.CallbackQuery, state: FSMContext):
    day = int(callback.data.split("_")[1])
    words = load_words(day)
    await state.update_data(day=day, words=words, index=0, correct=0, incorrect=0)
    await send_next_word(callback.message, state)

async def send_next_word(message, state: FSMContext):
    data = await state.get_data()
    words = data["words"]
    index = data["index"]

    if index >= len(words):
        correct = data["correct"]
        incorrect = data["incorrect"]
        day = data["day"]
        await message.answer(f"📊 Test tugadi!\n✅ To‘g‘ri: {correct}\n❌ Noto‘g‘ri: {incorrect}")
        save_to_db(day, correct, incorrect)
        await state.clear()
        return

    word = words[index]
    text = (
        f"🇺🇿 <b>{word['translation']}</b>\n"
        f"📘 {word['example']}\n\n"
        f"Bu so‘zning inglizchasini yozing yoki 'skip' deb yozing."
    )
    await message.answer(text)
    await state.set_state(LearningState.testing_words)

@dp.message(LearningState.testing_words)
async def handle_test_answer(message: types.Message, state: FSMContext):
    user_input = message.text.strip().lower()
    data = await state.get_data()
    words = data["words"]
    index = data["index"]
    correct = data["correct"]
    incorrect = data["incorrect"]
    correct_word = words[index]["word"].lower()
    mnemonics = load_mnemonics()

    if user_input == correct_word:
        await message.answer("✅ To‘g‘ri!")
        correct += 1
    elif user_input == "skip":
        await message.answer(f"⏭️ O‘tkazib yuborildi. To‘g‘ri javob: <b>{correct_word}</b>")
    else:
        await message.answer(f"❌ Noto‘g‘ri. To‘g‘ri javob: <b>{correct_word}</b>")
        incorrect += 1
        if correct_word in mnemonics:
            await message.answer(f"🧠 Esda saqlash usuli: {mnemonics[correct_word]}")

    await state.update_data(index=index + 1, correct=correct, incorrect=incorrect)
    await asyncio.sleep(0.5)
    await send_next_word(message, state)

def save_to_db(day, correct, incorrect):
    conn = sqlite3.connect("progress.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            day INTEGER PRIMARY KEY,
            correct INTEGER,
            incorrect INTEGER
        )
    """)
    cursor.execute("REPLACE INTO results (day, correct, incorrect) VALUES (?, ?, ?)", (day, correct, incorrect))
    conn.commit()
    conn.close()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
