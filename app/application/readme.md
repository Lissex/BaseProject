# 🧭 Application Layer (`app/application`)

Слой сценариев использования (use-case'ов). Оркестрирует domain и
infrastructure через их абстракции — сам не содержит бизнес-правил
(они в domain) и не знает про SQLAlchemy/FastAPI/JWT-библиотеки
напрямую (они за интерфейсами `UnitOfWork`/`PasswordHasher`/`TokenService`).

📌 **Dependency Rule**: application зависит от domain (через
интерфейсы), но не от infrastructure или api напрямую — конкретные
реализации приходят через Dependency Injection.

---

## 🧱 Структура

```
app/application/
├── dto/                    # Data Transfer Objects — входы/выходы use-case'ов
│   ├── register_user.py       # RegisterUserDTO
│   └── login.py                 # LoginDTO, TokenPairDTO
└── use_cases/               # Один класс = один сценарий использования
    ├── register_user.py         # RegisterUserUseCase
    ├── login.py                   # LoginUseCase
    ├── refresh_token.py            # RefreshTokenUseCase
    └── logout.py                    # LogoutUseCase (+ LogoutDTO)
```

---

## 📦 DTO — почему не Pydantic

DTO — обычные `@dataclass(frozen=True)`, не Pydantic-модели. Причина:
Pydantic-схемы запросов (`app/api/schemas/`) — это HTTP-специфичный
слой, а application не должен зависеть от FastAPI/Pydantic напрямую.
Конвертация "Pydantic-запрос → DTO" происходит в роуте (`app/api/routers/`).

---

## ⚙️ Use-case'ы

### `RegisterUserUseCase`
1. Оборачивает сырые строки в Value Objects (`Username`/`Email`/`PhoneNumber`)
   — **до** проверки уникальности, иначе нормализация регистра не
   применится, и `"John"`/`"john"` пройдут как разные значения.
2. Проверяет уникальность username/email/phone через `UserRepository`.
3. Хэширует пароль через `PasswordHasher`.
4. `User.create()` + `set_password()`, сохраняет через `UnitOfWork`.

Финальная защита от гонки (два одновременных запроса с одинаковым
username) — на уровне репозитория (`IntegrityError` → доменное
исключение), не в use-case.

### `LoginUseCase`
Вход по username **или** email. Намеренно единое исключение
`InvalidCredentials` и для "юзер не найден", и для "неверный пароль" —
чтобы не давать возможность перебором узнавать, какие
username/email вообще зарегистрированы (защита от enumeration).
`UserDisabled` проверяется **после** пароля — той же причине.

При успехе выпускает access-токен (JWT) и создаёт refresh-токен
(opaque, хранится в БД).

### `RefreshTokenUseCase`
Ротация: старый refresh-токен отзывается, выдаётся новый при каждом
обновлении. **Reuse detection** — если предъявлен уже отозванный
токен, это расценивается как возможная компрометация: отзываются
**все** refresh-токены пользователя, а не только предъявленный.
Отзыв коммитится, даже если use-case в итоге бросает исключение —
иначе "защитная" реакция откатилась бы вместе с ошибкой.

### `LogoutUseCase`
Идемпотентен: если токен не найден/уже неактивен — тихо завершается
без ошибки (цель "этим токеном нельзя пользоваться" уже достигнута).
Поддерживает `all_devices=True` для отзыва всех сессий пользователя.

---

## 🚨 Исключения, которые бросают use-case'ы

Только `DomainException`-наследники (`UsernameAlreadyExists`,
`InvalidCredentials`, `UserDisabled`, `InvalidPasswordFormat` и т.п.)
и `TokenException`-наследники (`InvalidToken`, `TokenExpired`,
`TokenRevoked`) — оба типа перехватываются одним `exception_handler`
в api-слое (см. [app/api/readme.md](../api/readme.md)).

---

## 🧪 Тестируемость

Use-case'ы тестируются без реальной БД/крипто — через `Fake`-реализации
интерфейсов (`tests/fakes.py`: `FakeUnitOfWork`, `FakeUserRepository`,
`FakePasswordHasher`, `FakeTokenService`), а не `unittest.mock.Mock`.
Причина: несколько последовательных вызовов внутри одного use-case
логически связаны (например, `create_user` должен быть виден в
следующем `get_by_id`) — с голыми моками пришлось бы вручную
прописывать `return_value` под каждый вызов.

```python
uow = FakeUnitOfWork()
use_case = RegisterUserUseCase(uow=uow, password_hasher=FakePasswordHasher())
user = await use_case.execute(dto)
assert uow.committed is True
```

---

## ⚠️ Важные замечания

1. **Use-case не открывает больше одной транзакции.** Один `async with
   self._uow` на весь сценарий — если нужно несколько репозиториев,
   они оба доступны через один и тот же `uow` (см. `UnitOfWork.readme`
   в domain-слое).
2. **Не пишите бизнес-правила в use-case.** Если правило про то, что
   считается валидным состоянием сущности — это домен (`User`,
   `RefreshToken`), а не application. Use-case — только оркестрация.
3. **Не импортируйте FastAPI/Pydantic/SQLAlchemy** в этом слое —
   единственные зависимости "наружу" — domain-интерфейсы.

← [Назад к общему README](../../README.md)