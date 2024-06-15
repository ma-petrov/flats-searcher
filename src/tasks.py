import re
import json
from typing import Optional
import requests
from datetime import datetime

from structlog import get_logger
from bs4 import BeautifulSoup

from repository import BaseRepository, PandasRepository
from api import reguest_with_proxy


logger = get_logger(__name__)


OOPS_MESSAGE = "Что-то пошло не так"
offer_link_pattern = re.compile(r"www.cian.ru/rent/flat/([0-9]+)")
summary_pattern = re.compile(r"Найдено (\d+) объявлени[еяй]")
time_pattern = re.compile(r"\d{2}:\d{2}")

# paths and urls
PATH = '/Users/petrov/Repositories/cian-flat-searcher/'
CIAN_URL = 'https://www.cian.ru/cat.php'
TELEGRAM_URL = 'https://api.telegram.org/bot'
TOKEN = "5132928323:AAG4BKwfB0ueNQmbmsgnBHZsF_OnjZ3Y2Bc"
CHAT_ID = "-1002236534227"


def new_offers_task():
    try:
        params = _load_params()
        logger.info("START_NEW_OFFERS_TASK", params=params)

        response = reguest_with_proxy(CIAN_URL, params)

        if bool(re.search(r'www.cian.ru/captcha', response.url)):
            logger.error("CIAN_BLOCKED_REQUEST")
            if (hour := datetime.now().hour) > 7 and hour < 23:
                _send_telegram("Циан заблокировал запрос капчей")
            return

        soup = BeautifulSoup(response.text, 'html.parser')

        if (offers_count := _get_offers_count(soup)) is None:
            return

        offer_ids = []
        articles = soup.findAll("article", attrs={"data-name": "CardComponent"})
        articles = articles[:offers_count]
        logger.info("ARTICLES_PARSED", articles_number=len(articles))

        for article in articles:
            offer_card = article.find("div", attrs={"data-testid": "offer-card"})
            offer_link = offer_card.find("a")["href"]

            if (searched := offer_link_pattern.search(offer_link)) is None:
                logger.error("INCORRECT_LINK", offer_link=offer_link)
                continue

            offer_id = searched.group(1)
            offer_ids.append(offer_id)

            # TODO: добавить поддержку сохранения даты публикации
            # date_container = article.find("div", attrs={"data-name": "TimeLabel"})
            # pub_date = date_container.find("span", text=time_pattern).text


        _save_and_send_new_offers(offer_ids)

    except Exception:
        logger.exception("PARSE_ERROR")
        _send_telegram(OOPS_MESSAGE)


def _get_offers_count(soup: BeautifulSoup) -> int | None:
    """Возвращает кол-во объявлений, найденных по фильтру.

    Тег div (data-name: CardComponent) содержит одно объявление квартиры.
    На странице показна результаты поиска по фильтру и рекомендуемые
    результаты в отдельных блоках, но их нельзя идентифицировать (нет
    красивого data-name или другого атрибута). Поэтому для того чтобы
    учитывались только объявления из фильтра, из списка объявлений
    берутся только первые N, где N - кол-во из блока SummaryHeader.
    """
    summary = soup.findAll("div", attrs={"data-name": "SummaryHeader"})

    if len(summary) > 1:
        logger.error("MULTIPLE_SUMMARY")
        return None

    if len(summary) == 0:
        logger.info("NO_NEW_OFFERS_SUMMARY")
        return None
    
    summary = summary[0].text
    
    if not (group := summary_pattern.search(summary)):
        logger.error("INCORRECT_SUMMERY", summary=summary)
        return None
    
    return int(group[1])


def _save_and_send_new_offers(
    ids: list[str | None],
    repository: Optional[BaseRepository] = None,
):
    """Вставляет новые id и отправляет в телеграм.
    
    Производит вставку новых id со статусом is_sent == False (если список ids
    пустой, то метод insert пропустит внутри себя вставку). Выбирает еще не
    отправленные id, пытается выполнить отправку. Если отправка была успешная,
    обновляет статус всем отправленным офферам на is_sent == True.
    """
    repository = repository or PandasRepository()
    repository.insert(ids)
    
    if not (offer_ids := repository.get_not_sent()):
        logger.info("ALL_OFFERS_SENT")
        return
    
    try:
        _send_offers(offer_ids)
        logger.info("NEW_OFFERS_SENT", offer_ids=offer_ids)
    except Exception:
        logger.exception("OFFERS_SENDING_ERROR")
    else:
        repository.update_sent(offer_ids)


def _send_offers(offer_ids: list[str]):
    offers = "\n".join(
        f"{i + 1} - https://www.cian.ru/rent/flat/{o}/"
        for i, o in enumerate(offer_ids)
    )
    _send_telegram(f"Новые объявления\n{offers}")


def _send_telegram(text: str):    
    class TelegramError(Exception):
        ...

    url = TELEGRAM_URL + TOKEN + '/sendMessage'
    data = {'chat_id': CHAT_ID, 'text': text}
    response = requests.post(url, data=data)
    
    if response.status_code != 200:
        logger.error("TELEGRAM_ERROR")
        raise TelegramError(response.text)


def _load_params():
    with open("params.json", "r") as f:
        return json.loads(f.read())
