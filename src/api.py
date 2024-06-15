from json import loads
from random import randint
from requests import get, Response
from pydantic import BaseModel
from structlog import get_logger


logger = get_logger(__name__)


PROXI_CONFIG_PATH = "proxies.json"


class Server(BaseModel):
    protocol: str
    address: str

class ProxyConfig(BaseModel):
    servers: list[Server]


def reguest_with_proxy(url: str, params: dict[str, str]) -> Response | None:
    '''
    Request with random proxy
    '''
    with open(PROXI_CONFIG_PATH, "r") as f:
        proxy_config = ProxyConfig(**loads(f.read()))

    random_proxy_number = randint(0, len(proxy_config.servers) - 1)
    proxy = proxy_config.servers[random_proxy_number]
    response = get(url=url, params=params, proxies={proxy.protocol: proxy.address})

    if response.status_code != 200:
        logger.error("CIAN_REQUEST_ERROR", response_text=response.text)
        return response
    
    logger.info("CIAN_REQUEST_DONE", url=response.url, proxy_address=proxy.address)

    return response