import json
import asyncio

from logging import getLogger
from typing import Dict
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.enums import ParseMode
import os
from dataclasses import dataclass
from datetime import datetime

from conf import BOT_TOKEN, WEBAPP_URL

# Configure logging
logger = getLogger(__name__)


# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Select Metro Stations",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )]
        ]
    )
    await message.answer(
        "Click the button below to select metro stations:",
        reply_markup=keyboard
    )

@router.message(lambda message: message.web_app_data)
async def handle_webapp_data(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        stations = data.get('selected_stations', [])
        
        if not stations:
            await message.answer("No stations were selected.")
            return

        response = "Selected stations:\n\n"
        for i, station in enumerate(stations, 1):
            response += f"{i}. {station}\n"
            
        await message.answer(response)
        
    except json.JSONDecodeError:
        await message.answer("Error: Invalid data received")
    except Exception as e:
        await message.answer(f"Error: {str(e)}")

dp.include_router(router)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

