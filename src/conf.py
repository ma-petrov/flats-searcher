from environs import Env


env = Env()


OOPS_MESSAGE = "Что-то пошло не так"

DEBUG = env.bool("DEBUG", False)

# database
POSTGRES_HOST = env.str("POSTGRES_HOST", "localhost")
POSTGRES_PASSWORD = env.str("POSTGRES_PASSWORD", "bot")
POSTGRES_URL = (
    f"postgresql+asyncpg://bot:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/bot"
)
MIGRATION_POSTGRES_URL = (
    f"postgresql+psycopg2://bot:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/bot"
)

# paths and urls
PATH = "/Users/petrov/Repositories/cian-flat-searcher/"
CIAN_URL = "https://www.cian.ru/cat.php"
TELEGRAM_URL = "https://api.telegram.org/bot"
BOT_TOKEN = env.str("TG_TOKEN", "")
TG_CHAT_ID = env.str("TG_CHAT_ID", "")
WEBAPP_URL = env.str("WEBAPP_URL", "localhost:8080")

# constants
FEE_THRESHOLD = 50
VIEWS_THRESHOLD = 100
