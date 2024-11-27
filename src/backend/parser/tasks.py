import re
import json

from datetime import datetime

from structlog import get_logger
from bs4 import BeautifulSoup

from parser.api import reguest_with_proxy
from parser.telegram import TelegramError, send_telegram
from conf import CIAN_URL, OOPS_MESSAGE, FEE_THRESHOLD, VIEWS_THRESHOLD
from models import User, Offer


logger = get_logger(__name__)


offer_link_pattern = re.compile(r"https://www.cian.ru/rent/flat/([0-9]+)")
offer_fee_pattern = re.compile(r"(\d+)%")
summary_pattern = re.compile(r"Найдено (\d+) объявлени[еяй]")
views_pattern = re.compile(r"(\d+) уникальны[хй]")
time_pattern = re.compile(r"\d{2}:\d{2}")


async def get_new_offers():
    params_file = "parser/params_100_new.json"

    try:
        params = _load_params(params_file)
        logger.info("START_NEW_OFFERS_TASK", params=params)

        response = reguest_with_proxy(CIAN_URL, params=params)

        if bool(re.search(r'www.cian.ru/captcha', response.url)):
            logger.error("CIAN_BLOCKED_REQUEST")
            if (hour := datetime.now().hour) > 7 and hour < 23:
                send_telegram("Циан заблокировал запрос капчей")
            return

        soup = BeautifulSoup(response.text, 'html.parser')

        if (offers_count := _get_offers_count(soup)) is None:
            return

        offers = []
        articles = soup.findAll("article", attrs={"data-name": "CardComponent"})
        articles = articles[:offers_count]
        logger.info("ARTICLES_PARSED", articles_number=len(articles))

        # Парсинг ссылок офферов
        offer_ids = []
        for article in articles:
            offer_card = article.find("div", attrs={"data-testid": "offer-card"})
            offer_link = offer_card.find("a")["href"]

            if (searched := offer_link_pattern.search(offer_link)) is None:
                logger.error("INCORRECT_LINK", offer_link=offer_link)
                continue

            offer_ids.append(int(searched.group(1)))

        # Ислключение офферов, которые уже есть в БД
        if not (offer_ids := await Offer.filter_new_offers(offer_ids)):
            return

        offers = [_parse_offer(i) for i in offer_ids]
        await _save_and_send_new_offers(offers)

    except Exception:
        logger.exception("PARSE_ERROR")
        send_telegram(OOPS_MESSAGE)


def _parse_offer(offer_id: int) -> Offer:
    offer = Offer(offer_id=offer_id)
    link = f"{offer.link}{offer_id}"

    response = reguest_with_proxy(link)
    offer_soup = BeautifulSoup(response.text, 'html.parser')

    # Парсинг кол-ва просмотров
    if stats := offer_soup.find(
        "button",
        attrs={"data-name": "OfferStats"},
    ):
        offer.stats = stats.text

    # Парсинг размера комиссии
    for offer_fact_item in offer_soup.findAll(
        "div",
        attrs={"data-name": "OfferFactItem"},
    ):
        if "Комисси" in offer_fact_item.text:
            fee_text = list(offer_fact_item)[2].text
            if (fee := offer_fee_pattern.search(fee_text)) is not None:
                offer.fee = int(fee.group(1))

    return offer


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


async def _save_and_send_new_offers(offers: list[Offer]):
    """Добавляет новые объявления в БД и отправляет в телеграм.

    Обновляет указатель на последнее отправленное объявление.
    Если в процессе отправки возникла ошибка, то указатель не
    обновляется.
    """
    if offers:
        await Offer.add_all(offers)

    user = await User.get()
    if not (user_offers := await user.get_new_offers()):
        return

    try:
        _send_offers(offers)
        await user.set_last_sent_offer_id(user_offers[-1].id)
    except TelegramError:
        pass


def _send_offers(offers: list[Offer]):
    for offer in offers:

        disable_notification = False

        if offer.fee is not None and offer.fee > FEE_THRESHOLD:
            logger.info("TOO_HIGH_FEE", offer=offer)
            continue

        if (
            (views := views_pattern.search(offer.stats)) is not None
            and int(views.group(1)) > VIEWS_THRESHOLD
        ):
            logger.info("TOO_MANY_VIEWS", offer=offer)
            disable_notification = True

        send_telegram(
            (
                f"{offer.stats}\n"
                f"Комиссия: {offer.fee or "NA"}%\n"
                f"{offer.link}{offer.offer_id}"
            ),
            disable_notification=disable_notification,
        )


def _load_params(params_file: str) -> dict:
    with open(params_file, "r") as f:
        return json.loads(f.read())
