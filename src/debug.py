import asyncio

from tasks import get_new_offers

asyncio.run(get_new_offers("params_100_new.json", "Двушки-трешки 100к"))
