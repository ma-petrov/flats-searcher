from json import loads
import json
from random import randint
from typing import Optional
from requests import get, Response
from pydantic import BaseModel
from structlog import get_logger

from parser.telegram import send_telegram


logger = get_logger(__name__)


PROXI_CONFIG_PATH = "parser/proxies.json"


class Server(BaseModel):
    protocol: str
    address: str

class ProxyConfig(BaseModel):
    servers: list[Server]


def reguest_with_proxy(
    url: str,
    params: Optional[dict[str, str]] = None
) -> Response | None:
    with open(PROXI_CONFIG_PATH, "r") as f:
        proxy_config = ProxyConfig(**loads(f.read()))

    random_proxy_number = randint(0, len(proxy_config.servers) - 1)
    proxy = proxy_config.servers[random_proxy_number]

    try:
        response = get(url=url, params=params, proxies={proxy.protocol: proxy.address})
    except ConnectionError:
        logger.error("CIAN_CONNECTION_ERROR")
        send_telegram("Ошибка соединения")
        return None

    if response.status_code != 200:
        logger.error("CIAN_RESPONSE_ERROR", response_text=response.text)
        return response
    
    logger.info("CIAN_REQUEST_DONE", url=response.url, proxy_address=proxy.address)

    return response
