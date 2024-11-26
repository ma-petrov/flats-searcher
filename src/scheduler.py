from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from structlog import get_logger
from parser.tasks import get_new_offers, send_telegram
from conf import DEBUG
import asyncio


logger = get_logger(__name__)


scheduler = AsyncIOScheduler()
scheduler.add_job(
    get_new_offers,
    trigger=IntervalTrigger(minutes=5),
    id='check_new_offers',
    name='Check for new offers every 5 minutes',
    replace_existing=True
)


async def main():
    try:
        logger.info("START_SCHEDULING")
        if not DEBUG:
            send_telegram("Начинаем парсить...")

        # почему-то шедулер сначала ждет 5 минут, поэтому запускаем сами 1 раз
        # чтобы не ждать 5 минут первого запуска
        await get_new_offers()

        scheduler.start()
        
        # Keep the main thread alive
        while True:
            await asyncio.sleep(1)
            
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler...")
        scheduler.shutdown()
    except Exception as e:
        logger.error(f"Error in scheduler: {e}")
        if not DEBUG:
            send_telegram(f"Error in scheduler: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
