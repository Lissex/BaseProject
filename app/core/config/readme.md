# ⚙️ Config Layer (`app/core/config`)

Единая точка входа для всех настроек приложения. Построена на
`pydantic-settings` с многоуровневым источником конфигурации и строгой
валидацией на старте — если конфиг неполный или сломан, приложение
падает сразу при импорте, а не где-то посреди обработки запроса.

---

## 🧱 Структура

```
app/core/config/
├── envs/                    # .env.<ENV> файлы с переменными окружения
│   ├── .env.example           # пример (коммитится)
│   ├── .env.dev                # не коммитится
│   ├── .env.prod                # не коммитится
│   └── .env.test                # не коммитится
├── yaml/                    # <ENV>.yaml файлы со структурными настройками
│   ├── .yaml.example
│   ├── dev.yaml
│   ├── prod.yaml
│   └── test.yaml
├── modules/                 # Pydantic-модели отдельных секций
│   ├── app.py                  # AppConfig
│   ├── database.py              # DatabaseConfig
│   └── jwt.py                    # JWTConfig
└── settings.py               # сборка Settings, выбор ENV, приоритет источников
```

---

## 🌍 Как выбирается окружение

Переменная `ENV` (`dev` / `prod` / `test`) читается из окружения ещё
**до** инициализации pydantic и валидируется по `Environment(StrEnum)`.
Невалидное значение — немедленный `RuntimeError` при импорте модуля,
а не молчаливый откат на дефолты.

| ENV | .env файл | yaml файл |
|-----|-----------|-----------|
| `dev` (по умолчанию) | `envs/.env.dev` | `yaml/dev.yaml` |
| `prod` | `envs/.env.prod` | `yaml/prod.yaml` |
| `test` | `envs/.env.test` | `yaml/test.yaml` |

Для `prod` оба файла **обязаны существовать** — иначе явный `RuntimeError`
при старте, а не тихая работа на дефолтах в проде.

---

## 🔌 Приоритет источников (сверху важнее)

```
init_settings        # значения, переданные вручную (тесты)
   ↓
env-переменные        # APP_<SECTION>__<FIELD>
   ↓
.env.<ENV> файл
   ↓
docker/k8s secrets
   ↓
<ENV>.yaml файл        # несекретные дефолты, самый низкий приоритет
   ↓
дефолты в полях моделей
```

**Секреты (пароли, JWT-ключ) никогда не должны лежать в yaml** — только
через env/secrets. `.yaml.example` явно это комментирует.

---

## 📐 Формат переменных окружения

```
APP_<SECTION>__<FIELD>
```

`APP_` — префикс, `__` — разделитель вложенности, `<SECTION>` — `APP` /
`DB` / `JWT`, регистр не важен. Примеры: `APP_APP__DEBUG`,
`APP_DB__PASSWORD`, `APP_JWT__SECRET_KEY`.

---

## 📦 Секции

| Модуль | Модель | Ключевые поля |
|---|---|---|
| `modules/app.py` | `AppConfig` | `TITLE`, `HOST`, `PORT`, `DEBUG` (default `False`), `LOG_LEVEL` |
| `modules/database.py` | `DatabaseConfig` | `USERNAME`, `PASSWORD: SecretStr` (без дефолта), `DATABASE`, `HOST`, `PORT`, `DRIVER`, `ECHO`; свойство `.url` собирает SQLAlchemy `URL` |
| `modules/jwt.py` | `JWTConfig` | `SECRET_KEY: SecretStr` (без дефолта), `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS` |

Все модели используют `extra="forbid"` — опечатка в имени поля в
`.env`/`.yaml` даёт явную ошибку при старте, а не тихий игнор.

---

## 🚀 Использование в коде

```python
from app.core.config.settings import settings

settings.app.DEBUG
settings.db.url
settings.jwt.ACCESS_TOKEN_EXPIRE_MINUTES
settings.is_prod  # bool
```

Для мест, где нужна возможность подмены конфига (тесты) — фабрика с
кэшем вместо готового объекта:

```python
from app.core.config.settings import get_settings

def get_db_url() -> str:
    return get_settings().db.url
```

---

## ⚠️ Частые ошибки

- **`Field required` при старте** — в `.env.<ENV>`/`<ENV>.yaml` не
  заполнено обязательное поле без дефолта (`db.PASSWORD`, `jwt.SECRET_KEY`).
- **`Extra inputs are not permitted`** — опечатка в названии поля
  (например `app.name` вместо `app.TITLE`) либо ключ в неверном регистре
  секции в yaml.
- **`Invalid ENV=...`** — переменная `ENV` не входит в `dev`/`prod`/`test`.

← [Назад к общему README](../../../README.md)