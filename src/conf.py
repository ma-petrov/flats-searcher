from environs import Env


env = Env()


OOPS_MESSAGE = "Что-то пошло не так"

DEBUG = env.bool("DEBUG", False)

# paths and urls
PATH = '/Users/petrov/Repositories/cian-flat-searcher/'
CIAN_URL = 'https://www.cian.ru/cat.php'
TELEGRAM_URL = 'https://api.telegram.org/bot'
TG_TOKEN = env.str("TG_TOKEN")
TG_CHAT_ID = env.str("TG_CHAT_ID")