# 🔌 Infrastructure Layer (`app/infrastructure`)

Реализует контракты (interfaces), объявленные в domain-слое: доступ к
БД, хранение refresh-токенов, хэширование паролей, работу с JWT.
Domain ничего не знает про SQLAlchemy/bcrypt/PyJWT — все конкретные
технологии живут только здесь.

📌 **Dependency Rule**: infrastructure зависит от domain (реализует его
интерфейсы), а не наоборот.

---

## 🧱 Структура

```
app/infrastructure/
├── database/
│   ├── models/            # SQLAlchemy ORM-модели ("плоские", не domain-объекты)
│   │   ├── user.py           # UserModel
│   │   └── refresh_token.py   # RefreshTokenModel
│   ├── base.py             # DeclarativeBase
│   ├── engine.py            # create_async_engine, get_db(), dispose_engine()
│   ├── unit_of_work.py       # SQLAlchemyUnitOfWork
│   └── alembic/               # миграции
├── mappers/                # domain.Entity <-> ORM Model
│   ├── user_mapper.py
│   └── refresh_token_mapper.py
├── repositories/            # реализации интерфейсов из domain/interfaces
│   ├── user_repository.py
│   └── refresh_token_repository.py
└── security/                 # реализации PasswordHasher / TokenService
    ├── password_hasher.py       # BcryptPasswordHasher
    ├── jwt_service.py            # JWTService (PyJWT)
    └── token_hasher.py            # SHA-256 для refresh-токенов
```

---

## 🗺️ ORM-модели vs Domain-сущности

ORM-модели (`database/models/`) намеренно "глупые" — обычные таблицы
без бизнес-логики. Вся логика живёт в domain (`User`, `RefreshToken`).
Между ними — слой `mappers/`:

```
UserModel (ORM) ──to_domain()──▶ User (domain)
User (domain)   ──to_model()──▶ UserModel (ORM), для create_user
User (domain)   ──update_model()──▶ мутирует уже загруженный UserModel, для update_user
```

Изменения через `update_model` идут in-place — иначе SQLAlchemy решит,
что это новая строка, и попытается сделать `INSERT` вместо `UPDATE`.

---

## 🗂️ Repository + Unit of Work

Оба паттерна реализуют интерфейсы из `app/domain/interfaces/`.

- `create_user`/`update_user`/`create` (refresh token) **не коммитят** —
  только `add`/`flush`. Коммит — ответственность `UnitOfWork`.
- `SQLAlchemyUserRepository.create_user` ловит `IntegrityError` и
  транслирует в доменные исключения (`UsernameAlreadyExists` и т.п.) —
  защита от гонки между проверкой уникальности в use-case и записью в БД.
- `SQLAlchemyUnitOfWork` создаёт новую `AsyncSession` на каждый вход в
  `async with` и передаёт её обоим репозиториям (`users`,
  `refresh_tokens`) — все изменения в рамках одного блока коммитятся
  или откатываются вместе.

```python
async with SQLAlchemyUnitOfWork() as uow:
    user = await uow.users.get_by_id(user_id)
    user.disable()
    await uow.users.update_user(user)
    await uow.commit()
```

Если `commit()` не вызван (в т.ч. из-за исключения) — базовый класс
`UnitOfWork.__aexit__` автоматически вызывает `rollback()`.

---

## 🔐 Security

| Файл | Что делает | Почему так |
|---|---|---|
| `password_hasher.py` | `BcryptPasswordHasher` — хэширует пароли пользователей | bcrypt, не passlib (активнее поддерживается); явно проверяет лимит в 72 байта вместо молчаливого обрезания |
| `jwt_service.py` | `JWTService` — выпускает/валидирует access-токен (JWT, stateless) | Короткоживущий (по умолчанию 15 мин), не требует похода в БД на каждый запрос |
| `token_hasher.py` | `generate_refresh_token()` / `hash_refresh_token()` | Refresh — **не** JWT, а opaque-строка (`secrets.token_urlsafe`), хранится в БД по SHA-256-хэшу. Детерминированный хэш нужен для `WHERE token_hash = ?` — bcrypt для этого не подходит (разная соль на каждый вызов) |

Access и refresh — разные механизмы намеренно: refresh всё равно
требует похода в БД ради возможности отзыва, поэтому JWT-обёртка для
него не даёт преимуществ, а opaque-токен + хэш проще и не хуже.

---

## 🧪 Тестируемость

Infrastructure тестируется либо через реальную БД (интеграционные
тесты, пока не написаны), либо не тестируется напрямую — она
покрывается косвенно через `Fake`-реализации тех же интерфейсов в
`tests/fakes.py`, которые используются в тестах application-слоя.

---

## ⚠️ Важные замечания

1. **Никогда не обращайтесь к `_identity`/`_security` domain-сущности
   напрямую** — только через публичные properties. Если нужного
   property нет, добавьте его в domain, а не обходите инкапсуляцию.
2. **Не коммитьте в репозиториях** — это ломает атомарность
   `UnitOfWork`, если один блок должен писать в несколько таблиц.
3. При добавлении новой ORM-модели — не забудьте импортировать её в
   `alembic/env.py`, иначе `autogenerate` её не увидит.

← [Назад к общему README](../../README.md)