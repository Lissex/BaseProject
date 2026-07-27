<div align="center">

# 🏗️ BaseApp

**Production-ready шаблон FastAPI-приложения на Clean Architecture + DDD**

*Domain-Driven Design · Clean Architecture · Async SQLAlchemy · JWT Auth · Docker*

</div>

---

## 📖 О проекте

BaseApp — не просто CRUD на FastAPI, а шаблон с настоящим разделением
слоёв: бизнес-логика (`domain`) не знает о существовании ни базы
данных, ни FastAPI, ни JWT-библиотек. Всё, что связывает их —
абстракции (`interfaces`), реализуемые в `infrastructure` и
собираемые в `api` через Dependency Injection.

Готовый рабочий пример — полноценный auth-контур: регистрация, вход,
access+refresh JWT с ротацией и reuse-detection, защищённые роуты —
как референс того, как строить любую следующую фичу поверх этого
скелета.

> 🚧 **Проект активно дописывается.** Auth-контур (register/login/
> refresh/logout/me) реализован и покрыт тестами на уровне domain и
> application. Остальное — по мере необходимости, см. раздел
> [«Известные ограничения / roadmap»](#-известные-ограничения--roadmap)
> внизу. Этот README и README каждого слоя обновляются вместе с кодом —
> если структура или решение из документа разошлись с тем, что видите
> в коде, актуальнее код, и README нужно поправить в том же PR.

---

## 🧠 Архитектура

```
                 ┌─────────────────────────┐
                 │   API (app/api)          │  ← FastAPI, роуты, DI, Pydantic
                 └────────────┬─────────────┘
                              │ вызывает
                 ┌────────────▼─────────────┐
                 │ Application (app/application) │  ← use-case'ы, DTO
                 └────────────┬─────────────┘
                              │ оперирует
                 ┌────────────▼─────────────┐
                 │   Domain (app/domain)     │  ← 💡 бизнес-логика, ядро
                 └────────────▲─────────────┘
                              │ реализует интерфейсы домена
                 ┌────────────┴─────────────┐
                 │ Infrastructure (app/infra) │  ← SQLAlchemy, bcrypt, PyJWT
                 └───────────────────────────┘
```

📌 **Dependency Rule**: стрелки зависимостей направлены **внутрь**, к
домену. Domain не импортирует ничего из внешних слоёв — ни `FastAPI`,
ни `SQLAlchemy`, ни `PyJWT`. Все конкретные технологии подключаются
через интерфейсы (`app/domain/interfaces/`) и внедряются в
`app/api/dependencies.py`.

Подробности и обоснования — в README каждого слоя:

| Слой | README | Что там |
|---|---|---|
| 🌐 API | [`app/api/readme.md`](app/api/readme.md) | Роуты, DI, exception handlers |
| 🧭 Application | [`app/application/readme.md`](app/application/readme.md) | Use-case'ы, DTO |
| 💡 Domain | [`app/domain/readme.md`](app/domain/readme.md) | Entities, Value Objects, интерфейсы |
| 🔌 Infrastructure | [`app/infrastructure/readme.md`](app/infrastructure/readme.md) | SQLAlchemy, репозитории, security |
| ⚙️ Config | [`app/core/config/readme.md`](app/core/config/readme.md) | Settings, окружения, .env/.yaml |

---

## 🛠️ Технологический стек

| Категория | Технология |
|---|---|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x (async, `asyncpg`) |
| Валидация/конфиг | Pydantic v2, `pydantic-settings` |
| Миграции | Alembic (async) |
| Auth | JWT access (PyJWT) + opaque refresh (БД, SHA-256) |
| Пароли | bcrypt |
| БД | PostgreSQL |
| Тесты | pytest, `pytest-asyncio`, `factory_boy` |
| Пакетный менеджер | `uv` |
| Контейнеризация | Docker (multi-stage), docker-compose |

---

## 🚀 Быстрый старт

### 1. Клонировать и поставить зависимости

```bash
uv sync
```

### 2. Настроить окружение

```bash
cp app/core/config/envs/.env.example app/core/config/envs/.env.dev
cp app/core/config/yaml/.yaml.example app/core/config/yaml/dev.yaml
```

Сгенерировать секреты:
```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"  # для APP_JWT__SECRET_KEY
```

Подробности по всем полям конфига — [`app/core/config/readme.md`](app/core/config/readme.md).

### 3. Поднять базу данных

```bash
make db-up
```

### 4. Применить миграции

```bash
make migrate
```

### 5. Запустить приложение

```bash
make run
```

Открыть **http://localhost:8000/docs** — интерактивная Swagger-документация.

### 6. Прогнать тесты

```bash
make test
```

Полный список команд — `make help`.

---

## 🔐 Auth-флоу (референсная реализация)

```
POST /auth/register  ──▶  RegisterUserUseCase  ──▶  User создан в БД

POST /auth/login      ──▶  LoginUseCase
                            ├── проверка пароля (bcrypt)
                            ├── access-токен (JWT, ~15 мин)
                            └── refresh-токен (opaque, ~30 дней, хэш в БД)

GET /users/me          ──▶  get_current_user (Depends)
   Authorization: Bearer <access_token>
                            └── decode JWT → user_id → загрузка User

POST /auth/refresh    ──▶  RefreshTokenUseCase
                            ├── старый refresh-токен ОТЗЫВАЕТСЯ (ротация)
                            ├── новая пара access+refresh
                            └── reuse detection: повторное использование
                                уже отозванного токена → отзыв ВСЕХ
                                токенов пользователя (подозрение на кражу)

POST /auth/logout     ──▶  LogoutUseCase
                            └── отзыв refresh-токена (одно устройство
                                или все — all_devices: true)
```

Access-токен — stateless JWT, не требует похода в БД на каждый запрос.
Refresh-токен — opaque-строка с хэшем в БД, что даёт реальную
возможность отзыва (logout, компрометация) без чёрных списков JWT.
Подробное обоснование этого решения — в
[`app/infrastructure/readme.md`](app/infrastructure/readme.md#-security).

---

## 📁 Структура проекта

```
BaseApp/
├── app/
│   ├── api/              # 🌐 FastAPI: роуты, схемы, DI
│   ├── application/       # 🧭 use-case'ы, DTO
│   ├── domain/              # 💡 сущности, VO, интерфейсы — ядро
│   ├── infrastructure/       # 🔌 SQLAlchemy, security, реализации
│   ├── core/
│   │   ├── config/              # ⚙️ Settings
│   │   └── exceptions/            # технические исключения (токены)
│   └── main.py                     # точка входа FastAPI
├── tests/
│   ├── unit/domain/                  # тесты Entities/VO
│   ├── unit/application/              # тесты use-case'ов (на Fake-объектах)
│   ├── factories.py                     # factory_boy фабрики тестовых данных
│   └── fakes.py                           # Fake UoW/репозитории/сервисы
├── docker-compose.yml     # Postgres для локальной разработки
├── Dockerfile               # multi-stage сборка приложения
├── Makefile                   # команды: run, db-up, migrate, test, lint...
└── pytest.ini
```

---

## 🧪 Тестирование

Domain и application слои покрыты unit-тестами без обращения к
реальной БД:

- **Domain** (`tests/unit/domain/`) — Value Objects и `User` entity,
  включая регрессионные тесты на исправленные баги (нормализация,
  сохранение полей при частичном изменении identity).
- **Application** (`tests/unit/application/`) — все 4 use-case'а auth-
  контура, через `Fake`-реализации интерфейсов (`tests/fakes.py`), а не
  `unittest.mock` — это даёт тестам связность реального поведения
  (данные, созданные в одном вызове, видны в следующем) без
  избыточной ручной настройки моков.
- **Тестовые данные** — через `factory_boy` (`tests/factories.py`):
  валидные объекты по умолчанию, с возможностью переопределить только
  нужное поле для конкретного теста.

```bash
make test
```

Подробнее о паттернах тестирования — в README `domain` и `application`
слоёв.

---

## 🗺️ Дизайн-решения, которые стоит знать

Эти решения не всегда очевидны из самого кода — стоит понимать
рассуждение за ними, прежде чем менять или "упрощать".

### Архитектура и границы слоёв

- **Repository + Unit of Work, а не SQLAlchemy-сессия напрямую в
  use-case.** Репозитории скрывают ORM от application и domain; UoW
  гарантирует, что несколько репозиториев в одном сценарии
  коммитятся/откатываются атомарно вместе. Один `async with uow` —
  одна транзакция на весь use-case.
- **DTO — обычные `@dataclass`, не Pydantic.** Application-слой не
  должен зависеть от FastAPI/Pydantic. Конвертация "Pydantic-запрос →
  DTO" происходит в роуте, не глубже.
- **`extra="forbid"` во всех конфиг-моделях.** Опечатка в `.env`/`.yaml`
  (например `name` вместо `TITLE`) должна падать явной ошибкой при
  старте, а не тихо игнорироваться — тихий игнор один раз реально
  привёл к тому, что изменение конфига не применялось незаметно.
- **Domain не имеет прямого доступа `_identity`/`_security` снаружи.**
  Только через properties. Если нужного property не хватает — его
  добавляют в domain-класс, а не обходят инкапсуляцию из mapper'а или
  use-case (в infrastructure это уже один раз случайно произошло и
  было исправлено).

### Auth

- **Access — JWT (stateless), refresh — opaque-строка в БД.** Refresh
  всё равно требует похода в БД ради возможности отзыва (logout,
  компрометация) — JWT-обёртка для него не даёт преимуществ, только
  сложность. Opaque `secrets.token_urlsafe` + SHA-256-хэш в
  индексируемой колонке — проще и не хуже.
- **SHA-256 для refresh-токена, bcrypt — для пароля.** Разные цели:
  bcrypt намеренно недетерминирован (соль на каждый вызов) — это плюс
  для паролей (защита от rainbow tables), но делает невозможным поиск
  `WHERE token_hash = ?`. Refresh-токен — уже 512 бит случайности,
  не то, что нужно защищать от перебора по словарю, детерминированный
  SHA-256 — осознанный компромисс, не недосмотр.
- **Refresh-токен ротируется при каждом использовании + reuse
  detection.** Повторное предъявление уже отозванного refresh-токена
  трактуется как признак кражи — отзываются ВСЕ токены пользователя,
  а не только предъявленный. Этот массовый отзыв коммитится ДО того,
  как use-case бросает исключение — иначе "защитная" реакция сама
  откатилась бы автоматическим rollback при выходе из `async with`.
- **`InvalidCredentials` — один и тот же ответ и для "юзера нет", и
  для "пароль неверный".** Раскрытие разницы — это canonical
  enumeration-уязвимость (позволяет перебором узнать существующие
  username/email). `UserDisabled` при этом проверяется только ПОСЛЕ
  пароля — той же причине.
- **`DomainException` и `TokenException` — разные базовые классы.**
  Бизнес-ошибки домена (`UsernameAlreadyExists`) и технические ошибки
  аутентификации (`InvalidToken`) концептуально разные вещи, хотя
  обрабатываются одним HTTP exception_handler'ом (одинаковая форма
  `message`/`status_code`).

### Тесты

- **`Fake`-объекты, а не `unittest.mock.Mock`, для тестов
  use-case'ов.** Несколько вызовов внутри одного use-case логически
  связаны (`create_user`, потом `get_by_id` должен это увидеть) — с
  голыми моками пришлось бы вручную дублировать `return_value` под
  каждый вызов, и тесты не отражали бы реальную связность данных.
- **`factory_boy`-фабрики генерируют валидные данные по построению**,
  а не через `Faker` напрямую там, где формат жёстко ограничен regex'ом
  (username, телефон) — случайный сгенерированный Faker'ом username с
  точкой внутри дал бы flaky-тест, падающий не по вине тестируемого
  кода.

---

## 🧩 Известные ограничения / roadmap

- [ ] Rate limiting на `/auth/login` — рассматривался, отложен
- [ ] Интеграционные тесты (реальная БД в CI)
- [ ] `app/api` пока без собственных тестов (только через use-case тесты + ручная проверка)
- [ ] Redis — не подключён (нет задач, где он пока нужен)
- [ ] CI-пайплайн (lint + test на push)

---

## 📜 Лицензия

Внутренний шаблон проекта — уточните лицензию перед публикацией вовне.