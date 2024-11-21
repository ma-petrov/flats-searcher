from contextlib import suppress
import pytest_asyncio
from sqlalchemy import create_engine

from conf import MIGRATION_POSTGRES_URL
from models import BaseModel


@pytest_asyncio.fixture(scope="function", autouse=True)
def clear_database(request):
    if not request.node.get_closest_marker("db"):
        yield
        return

    engine = create_engine(MIGRATION_POSTGRES_URL, echo=False)
    
    BaseModel.metadata.drop_all(engine)
    BaseModel.metadata.create_all(engine)

    with suppress():
        yield

    BaseModel.metadata.drop_all(engine, checkfirst=True)
    BaseModel.metadata.create_all(engine)
