from time import sleep
from schedule import every, run_pending
from structlog import get_logger
from tasks import new_offers_task


logger = get_logger(__name__)


every(5).minutes.do(new_offers_task)


logger.info("START_SHEDULING")
while True:
    run_pending()
    sleep(1)
