import json
import asyncio

from logging import getLogger
from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from conf import BOT_TOKEN, WEBAPP_URL


logger = getLogger(__name__)


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Метро", web_app=WebAppInfo(url=WEBAPP_URL))
    await message.answer(
        "Настройки",
        reply_markup=builder.as_markup()
    )


dp.include_router(router)


logger.info("Starting bot")
asyncio.run(dp.start_polling(bot))
