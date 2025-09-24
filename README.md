# Аналитика транзакций (курсовой)


Приложение читает Excel с транзакциями, готовит JSON для веб-страниц, формирует отчёты и предоставляет сервисы.


## Быстрый старт
```bash
# Установите Poetry и зависимости
poetry install


# Скопируйте .env_template в .env и заполните при необходимости
cp .env_template .env


# Добавьте свой файл с транзакциями
mkdir -p data && cp /путь/к/operations.xlsx data/operations.xlsx


# Запуск линтеров и тестов
poetry run flake8
poetry run isort --check-only .
poetry run black --check .
poetry run mypy src
poetry run pytest
## Использование CLI

После установки зависимостей и подготовки данных можно запускать приложение из консоли:

```bash
poetry run python -m src.main <команда> [аргументы]
