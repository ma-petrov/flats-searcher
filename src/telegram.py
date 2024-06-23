import requests

from structlog import get_logger

from conf import TELEGRAM_URL, TG_TOKEN, TG_CHAT_ID


logger = get_logger(__name__)


def send_telegram(text: str):    
    class TelegramError(Exception):
        ...

    url = TELEGRAM_URL + TG_TOKEN + '/sendMessage'
    data = {'chat_id': TG_CHAT_ID, 'text': text}
    response = requests.post(url, data=data)
    
    if response.status_code != 200:
        logger.error("TELEGRAM_ERROR")
        raise TelegramError(response.text)
