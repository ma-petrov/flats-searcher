import json
import asyncio
import logging

from aiogram import F, Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from conf import BOT_TOKEN, WEBAPP_URL


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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


@router.message(F.web_app_data)
async def handle_webapp_data(message: Message):
    data = json.loads(message.web_app_data.data)
    logger.info(data)


dp.include_router(router)
asyncio.run(dp.start_polling(bot))
