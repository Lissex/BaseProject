# Конфигурация проекта

## ⚠️ Отличие от черновика

Ваш черновик описывает структуру `.base.yaml` / `local.yaml` / единый `.env` — это **не
соответствует** текущей реализации `settings.py`. Сейчас конфиг завязан на переменную
`ENV` (`dev` / `prod` / `test`) и подгружает файлы `.env.<ENV>` и `<ENV>.yaml` отдельно
для каждого окружения. README ниже описывает то, что реально реализовано. Если нужна
именно схема `base + local` — это отдельная переработка `settings.py`, дайте знать.

## Структура

```
app/core/config/
├── envs/                  # .env.<ENV> файлы с переменными окружения
│   ├── .env.example       # пример (коммитится)
│   ├── .env.dev           # локальные настройки (не коммитится)
│   ├── .env.prod          # прод-настройки (не коммитится)
│   └── .env.test          # тестовые настройки (не коммитится)
├── yaml/                  # <ENV>.yaml файлы со структурными настройками
│   ├── .yaml.example      # пример (коммитится)
│   ├── dev.yaml
│   ├── prod.yaml
│   └── test.yaml
├── modules/                # Pydantic-модели отдельных секций конфига
│   ├── app.py               # AppConfig
│   └── database.py          # DatabaseConfig
└── settings.py              # сборка Settings, выбор ENV, приоритет источников
```

> `.env.*` и `<ENV>.yaml` (кроме `.example`) исключены из git через `.gitignore` —
> в репозитории должны быть только `.env.example` и `.yaml.example`.

## Как выбирается окружение

Переменная `ENV` читается **до** инициализации pydantic (`os.getenv("ENV", "dev")`) и
валидируется по `Environment` (`dev` / `prod` / `test`). Невалидное значение (например
`ENV=produ`) роняет приложение сразу при импорте, с явным сообщением об ошибке —
это сделано намеренно, чтобы не подниматься "непонятно в каком" окружении.

От `ENV` зависит, какие файлы подхватятся:

| ENV | .env файл | yaml файл |
|-----|-----------|-----------|
| `dev` (по умолчанию) | `envs/.env.dev` | `yaml/dev.yaml` |
| `prod` | `envs/.env.prod` | `yaml/prod.yaml` |
| `test` | `envs/.env.test` | `yaml/test.yaml` |

**Для `prod` оба файла обязаны существовать** — если один из них отсутствует,
приложение падает при старте с явной ошибкой, а не тихо продолжает работу
на дефолтах модели.

## Приоритет источников (сверху важнее)

1. `init_settings` — значения, переданные вручную при создании `Settings(...)` (тесты)
2. Переменные окружения (`APP_...`)
3. `.env.<ENV>` файл
4. Docker/k8s secrets (`file_secret_settings`)
5. `<ENV>.yaml` файл
6. Дефолты, заданные прямо в полях `AppConfig` / `DatabaseConfig`

Т.е. yaml — это база с несекретными дефолтами, а env-переменные и `.env` её
переопределяют. Секреты (пароли, ключи) должны приходить только через env/secrets,
никогда не должны лежать в yaml.

## Формат переменных окружения

```
APP_<SECTION>__<FIELD>
```

- `APP_` — префикс (`env_prefix` в `Settings.model_config`)
- `__` — разделитель вложенности (`env_nested_delimiter`)
- `<SECTION>` — `APP` (для `AppConfig`) или `DB` (для `DatabaseConfig`)
- `<FIELD>` — имя поля модели, регистр не важен (`case_sensitive=False`)

Примеры: `APP_APP__DEBUG`, `APP_APP__LOG_LEVEL`, `APP_DB__PASSWORD`, `APP_DB__HOST`.

Полный список переменных — см. `envs/.env.example`.

## modules/ — секции конфига

| Файл | Модель | Назначение |
|------|--------|------------|
| `app.py` | `AppConfig` | название, host/port приложения, `DEBUG`, `LOG_LEVEL` |
| `database.py` | `DatabaseConfig` | подключение к БД, включая `PASSWORD: SecretStr` без дефолта |

Обе модели используют `extra="forbid"` — опечатка в имени поля в `.env`/`.yaml`
(например `name` вместо `TITLE`) даёт явную ошибку при старте вместо тихого игнора.

`DatabaseConfig.url` — `@property`, собирающая SQLAlchemy `URL` из отдельных полей
(`USERNAME`, `PASSWORD`, `HOST`, `PORT`, `DATABASE`, `DRIVER`). Задавать `url` напрямую
через конфиг нельзя — такого поля нет.

## Использование в коде

```python
from app.core.config.settings import settings

settings.app.DEBUG
settings.db.url
settings.is_prod  # bool
```

Для мест, где нужна возможность подмены конфига (тесты), используйте фабрику
с кэшем вместо готового объекта:

```python
from app.core.config.settings import get_settings

def get_db_url() -> str:
    return get_settings().db.url
```

## Известные ограничения / TODO

- `Redis` и `JWT` конфиги упоминались в черновике `.env.example`, но модулей для них
  пока нет (`RedisConfig`, `JWTConfig` не реализованы и не подключены в `Settings`).
  Добавлять переменные `APP_REDIS__*` / `APP_JWT__*` в `.env` сейчас бессмысленно —
  они будут молча проигнорированы (`extra="ignore"` на уровне `Settings`).
- `POOL_SIZE` для БД не конфигурируется через `DatabaseConfig` — сейчас захардкожен
  в `app/infrastructure/database/engine.py` (`10 if is_prod else 5`).