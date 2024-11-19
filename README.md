## Запуск

### Запуск локально

1. Поднять инфраструктуру `docker compose up --build -d`
2. Запустить миграцию БД `alembic upgrade head`
3. Запустить бот `python sheduler.py`

### Запуск локально полностью в docker

1. Создать .loca.env файл:
```
TG_TOKEN="<токен бота>"
TG_CHAT_ID="<id канала>"
DEBUG="False"
```

2. `docker compose --env-file=.local.env --profile app up --build -d`

## Создание миграций
`alembic revision --autogenerate -m "<название миграции>"`

## Откат миграций
`alembic downgrade -1`
