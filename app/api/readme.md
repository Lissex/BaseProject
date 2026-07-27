# 🌐 API Layer (`app/api`)

Единственный слой, который знает про HTTP: FastAPI-роуты, Pydantic-схемы
запросов/ответов, dependency injection, перевод исключений в HTTP-ответы.
Всё остальное (application, domain, infrastructure) ничего не знает
про существование FastAPI.

📌 **Dependency Rule**: api зависит от application (вызывает use-case'ы)
и собирает конкретные реализации infrastructure для DI — это
единственное место, где происходит "сборка" всего приложения.

---

## 🧱 Структура

```
app/api/
├── schemas/                 # Pydantic-модели запросов/ответов
│   ├── auth.py                 # RegisterRequest/Response, LoginRequest, TokenResponse, ...
│   └── user.py                   # UserResponse
├── routers/
│   ├── auth.py                 # /auth/register, /login, /refresh, /logout
│   └── users.py                  # /users/me (защищённый роут)
├── dependencies.py           # DI: UoW, PasswordHasher, TokenService, use-case providers, get_current_user
└── exception_handlers.py     # DomainException/TokenException/ValidationError/Exception → HTTP
```

---

## 🔌 Dependency Injection

`dependencies.py` — единственное место, где создаются конкретные
реализации (`SQLAlchemyUnitOfWork`, `BcryptPasswordHasher`, `JWTService`)
и передаются в use-case'ы через `Depends`.

```python
def get_uow() -> UnitOfWork:
    return SQLAlchemyUnitOfWork()   # новый UoW на каждый запрос — своя сессия

@lru_cache
def get_password_hasher() -> PasswordHasher:
    return BcryptPasswordHasher()   # без состояния — можно кэшировать на процесс
```

`get_current_user` — dependency для защищённых роутов: достаёт
`Authorization: Bearer <token>`, валидирует через `TokenService`,
подгружает `User` через `UoW`. Используется так:

```python
@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    ...
```

---

## 🚨 Exception Handlers

Единая точка перевода ошибок в HTTP, все — в формате `{"detail": ...}`:

| Тип исключения | Откуда | HTTP-код |
|---|---|---|
| `DomainException` | domain (бизнес-ошибки: `UsernameAlreadyExists`, `UserDisabled`...) | из `exc.status_code` (400/401/403/404/409) |
| `TokenException` | `app/core/exceptions/token.py` (технические: `InvalidToken`, `TokenExpired`, `TokenRevoked`) | 401 |
| `RequestValidationError` | FastAPI/Pydantic — невалидное тело запроса | 422 |
| `Exception` (всё остальное) | непойманный баг | 500, детали скрыты в `is_prod` |

`DomainException` и `TokenException` — разные базовые классы (первый —
бизнес-логика, второй — техническая проблема аутентификации), но одной
формы (`message`/`status_code`), поэтому обрабатываются одним и тем же
handler'ом.

---

## 🛣️ Роуты

| Метод | Путь | Auth | Назначение |
|---|---|---|---|
| `POST` | `/auth/register` | — | Регистрация |
| `POST` | `/auth/login` | — | Вход, выдаёт access+refresh |
| `POST` | `/auth/refresh` | — (refresh-токен в теле) | Обновление access, ротация refresh |
| `POST` | `/auth/logout` | — (refresh-токен в теле) | Отзыв refresh-токена (одно устройство/все) |
| `GET` | `/users/me` | Bearer access-токен | Данные текущего пользователя |

Refresh-токен передаётся в теле JSON-запроса, не в cookie — конечный
потребитель этого API (например BFF) сам решает, как упаковывать
токены для браузера.

---

## 🧪 Тестируемость

API-слой пока не покрыт тестами напрямую (только вручную через
`/docs`) — логика уже протестирована на уровне use-case'ов
(`app/application/readme.md`), роуты — тонкая обвязка поверх них.
Для end-to-end тестов сюда напрашивается `httpx.AsyncClient` +
`ASGITransport` поверх `app/main.py`.

---

## ⚠️ Важные замечания

1. **Не пишите бизнес-логику в роутах.** Роут только конвертирует
   Pydantic-запрос → DTO → вызывает use-case → конвертирует результат
   в Pydantic-ответ.
2. **Не ловите `DomainException` в роутах вручную** — это уже делает
   `exception_handlers.py` глобально.
3. **`HTTPBearer(auto_error=False)`**, не дефолтный `auto_error=True` —
   иначе отсутствие заголовка `Authorization` даёт ответ в формате
   FastAPI, а не в едином `{"detail": ...}`.

← [Назад к общему README](../../README.md)