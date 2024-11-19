from __future__ import annotations
from typing import Optional

from sqlalchemy import ForeignKey, func, select
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)

from conf import POSTGRES_URL
from sqlalchemy import update


async_engine = create_async_engine(POSTGRES_URL, echo=True)
async_session = async_sessionmaker(async_engine, expire_on_commit=False)


class BaseModel(AsyncAttrs, DeclarativeBase):
    """Базовые методы чтения, записи в БД"""

    @classmethod
    async def execute(cls, query):
        async with async_session() as session:
            result = await session.execute(query)
            await session.commit()
            return result

    @classmethod
    async def add_all(cls, bulk_list: list[BaseModel]):
        async with async_session() as session:
            session.add_all(bulk_list)
            await session.commit()

    async def add(self):
        async with async_session() as session:
            session.add(self)
            await session.commit()


class Offer(BaseModel):
    __tablename__ = "offer"

    id: Mapped[int] = mapped_column(primary_key=True)
    offer_id: Mapped[str]
    link: Mapped[str]
    fee: Mapped[int]

    @classmethod
    async def get_last_offer_id(cls):
        query = select(func.max(cls.id))
        return await cls.execute(query)


class User(BaseModel):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    last_sent_offer_id: Mapped[int]
    username: Mapped[str]

    @classmethod
    async def get(self):
        # костыль временно для одного канала
        async with async_session() as session:
            if user := await session.get(User, 1):
                return user

            user = User(id=1, last_sent_offer_id=0, username="clipdecliprepeat")
            await user.add()
            return user

    async def get_new_offers(self):
        """Возвращает список новых объявлений для пользователя."""
        query = (
            select(Offer)
            .where(Offer.id > self.last_sent_offer_id)
            .order_by(Offer.id)
        )
        result = await Offer.execute(query)
        return result.scalars().all()

    async def set_last_sent_offer_id(self, offer_id: int):
        self.last_sent_offer_id = offer_id
        await self.add()
