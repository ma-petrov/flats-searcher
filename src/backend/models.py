from __future__ import annotations

from sqlalchemy import func, select, Integer, cast, ARRAY
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
)

from conf import POSTGRES_URL


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
    offer_id: Mapped[int] = mapped_column(unique=True)
    fee: Mapped[int] = mapped_column(nullable=True)
    stats: Mapped[str] = mapped_column(default="")

    @property
    def link(self) -> str:
        return "https://www.cian.ru/rent/flat/"

    @classmethod
    async def get_last_offer_id(cls):
        query = select(func.max(cls.id))
        return await cls.execute(query)
    
    @classmethod
    async def filter_new_offers(cls, offer_ids: list[int]) -> list[int | None]:
        """Возвращает список идентификаторов объявлений, которых нет в БД."""
        ids = cast(offer_ids, ARRAY(Integer))
        cte = select(func.unnest(ids).column_valued("offer_id"))
        query = (
            select(cte.c.offer_id)
            .select_from(cte)
            .join(cls, onclause=cte.c.offer_id == cls.offer_id, isouter=True)
            .where(cls.offer_id == None)
            .order_by(cte.c.offer_id)
        )
        result = await cls.execute(query)
        return result.scalars().all()


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
