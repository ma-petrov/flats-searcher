import requests

from structlog import get_logger

from conf import TELEGRAM_URL, BOT_TOKEN, TG_CHAT_ID, DEBUG


logger = get_logger(__name__)


class TelegramError(Exception):
    pass


def send_telegram(
    text: str,
    disable_notification: bool | None = False,
):
    url = TELEGRAM_URL + BOT_TOKEN + "/sendMessage"
    data = {
        "chat_id": TG_CHAT_ID, 
        "text": text,
        "disable_notification": disable_notification,
    }

    if DEBUG:
        logger.info("MESSAGE_SENT", text=text)
        return
    
    try:
        response = requests.post(url, data=data)
    except ConnectionError:
        logger.error("TELEGRAM_ERROR", type="CONNECTION")

        # raise TelegramError
    except Exception:
        logger.exception("TELEGRAM_ERROR", type="UNKNOWN")
        # raise TelegramError
    
    if response.status_code != 200:
        logger.error("TELEGRAM_ERROR", type="RESPONSE", json=response.json())
        raise TelegramError
