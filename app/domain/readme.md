# 📦 Domain Layer (`app/domain`)

Доменный слой — это ядро системы, реализующее бизнес-логику в соответствии с принципами:

* **DDD (Domain-Driven Design)**
* **Clean Architecture**

Он не зависит от:

* базы данных
* фреймворков (FastAPI и т.д.)
* инфраструктуры

---

## 🧠 Роль в архитектуре

```
API (app/api)
      ↓
Application (app/application)
      ↓
Domain (app/domain)   ← 💡 Бизнес-логика
      ↑
Infrastructure (app/infra)
```

📌 **Dependency Rule**: зависимости направлены внутрь
→ Domain не зависит ни от одного слоя

---

## 🎯 Задачи доменного слоя

* Описание бизнес-модели
* Гарантия инвариантов
* Инкапсуляция бизнес-логики
* Формирование Ubiquitous Language
* Определение контрактов (interfaces)

---

## 🧱 Структура

```
app/domain/
├── entities/        # Сущности и агрегаты
├── value_objects/   # Value Objects
├── exceptions/      # Доменные исключения
├── interfaces/       # Контракты (репозитории, unit of work)
```

---

# 🧑‍💻 Entities и Aggregate Root

## User — агрегатный корень

User управляет:

* идентификацией (identity)
* безопасностью (security)

---

## 📦 Состав агрегата

```
User
├── id: UUID
├── identity: UserIdentity
│   ├── username: Username
│   ├── email: Email
│   └── phone: PhoneNumber
│
├── security: UserSecurity
│   ├── hashed_password
│   ├── is_active
│   └── is_email_verified
│
├── created_at
└── updated_at
```

Все поля агрегата доступны снаружи только через properties
(`user.username`, `user.email`, `user.is_active`, `user.is_email_verified` и т.д.) —
прямого доступа к `_identity`/`_security` быть не должно нигде за пределами `User`.

---

## ⚙️ Создание пользователя

```python
user = User.create(
    username="john_doe",
    email="john@mail.com",
    phone="+79991234567"
)
```

📌 Используется factory method:

* генерируется UUID
* валидируются VO
* задаются начальные значения

---

## 🔄 Поведение (Rich Domain Model)

Вся логика находится внутри сущности:

```python
user.disable()
user.enable()
user.verify_email()
user.set_password(hash)
```

❌ Нельзя:

```python
user.is_active = False
```

---

## ✏️ Изменение данных

```python
user.change_username("new_name")
user.change_email("new@mail.com")
user.change_phone("+79991234567")
```

📌 Правила:

* email → сбрасывает верификацию (`is_email_verified = False`)
* всегда обновляется `updated_at`
* новое значение всегда оборачивается в соответствующий VO
  (`Username`/`Email`/`PhoneNumber`) — валидация формата отрабатывает
  при каждом изменении, а не только при `User.create()`
* остальные поля `identity` (username/email/phone) при изменении одного
  из них берутся из текущего состояния (`self.username`, `self.email`,
  `self.phone`), а не теряются — `UserIdentity` пересобирается целиком,
  так как VO иммутабелен

---

## 🧠 Инварианты

* Username / Email / Phone всегда валидны
* Пароль не может быть пустым
* Email требует повторной верификации при изменении
* Состояние пользователя управляется только методами

---

# 🧩 Value Objects

## 📌 Характеристики

* Иммутабельны (`frozen=True`)
* Не имеют identity
* Валидируются при создании
* Сравниваются по значению

---

## 📧 Email

* Валидация через regex
* Предоставляет `domain`

```python
email.domain
```

---

## 📱 PhoneNumber

* Нормализует номер
* Приводит к формату: `+79991234567`

---

## 👤 Username

* lowercase
* 3–20 символов
* только `[a-z0-9_]`

---

## 🔗 Композитные VO

### UserIdentity

Содержит:

* username
* email
* phone

Все три поля обязательны и не имеют дефолтов — при пересборке
(`change_username`/`change_email`/`change_phone`) нужно передавать все три,
даже если меняется только одно.

### UserSecurity

Содержит:

* hashed_password
* is_active
* is_email_verified

---

# 🚨 Domain Exceptions

## 📌 Назначение

* Явное выражение бизнес-ошибок
* Изоляция от HTTP слоя
* Использование в application

---

## 🧱 Базовый класс

```python
class DomainException(Exception)
```

Содержит:

* message
* status_code

---

## 📚 Примеры

* UsernameAlreadyExists
* EmailAlreadyExists
* UserNotFound
* UserDisabled
* InvalidEmailFormat
* InvalidUsernameFormat
* InvalidPhoneFormat
* EmailNotVerified

---

## 💡 Важно

Domain слой:

* не знает про HTTP
* но может отдавать `status_code` для маппинга

---

# 🗂️ Interfaces

Домен определяет два контракта, которые реализует infrastructure-слой.

## UserRepository

Контракт для доступа к данным пользователя.

```python
async def get_by_id(user_id: UUID) -> User | None
async def get_by_username(username: str) -> User | None
async def get_by_email(email: str) -> User | None

async def create_user(user: User) -> None
async def update_user(user: User) -> None
```

⚠️ Запрещено:

* использовать ORM-специфичные типы в сигнатурах
* писать SQL
* добавлять бизнес-логику

`create_user`/`update_user` не коммитят транзакцию — это ответственность
`UnitOfWork`.

## UnitOfWork

Контракт границы транзакции. Инкапсулирует набор репозиториев,
работающих в рамках одной транзакции, и явный commit/rollback.

```python
async with uow:
    user = await uow.users.get_by_id(user_id)
    user.disable()
    await uow.users.update_user(user)
    await uow.commit()
```

Правила:

* если `commit()` не вызван явно (в т.ч. из-за исключения внутри блока) —
  при выходе из `async with` происходит автоматический `rollback()`
* репозитории (`uow.users` и т.д.) доступны только внутри блока
  `async with` — обращение к ним до входа или после выхода не гарантировано
* один `UnitOfWork` = одна транзакция для всех репозиториев внутри него

Реализация (`SQLAlchemyUnitOfWork` и т.п.) находится в infrastructure-слое,
домен знает только абстрактный контракт.

---

# 🧪 Тестируемость

Домен тестируется:

* без базы данных
* без FastAPI
* без моков инфраструктуры

---

# 🔥 Ключевые принципы

## 1. Dependency Rule

Domain — самый независимый слой

---

## 2. Rich Domain Model

Логика внутри сущностей

---

## 3. Инварианты защищены

* через VO
* через методы Entity

---

# ⚠️ Важные замечания

## 1. Всегда используйте Value Objects

❌ Неправильно:

```python
UserIdentity(username=new_username)
```

✅ Правильно:

```python
UserIdentity(
    username=Username(new_username),
    email=Email(...),
    phone=PhoneNumber(...)
)
```

## 2. Не теряйте данные при изменениях

При изменении одного поля:
→ остальные должны сохраняться (передавайте текущее значение через
properties, например `self.email`, `self.phone`, а не оставляйте поле
незаполненным)

## 3. Не обращайтесь к приватным атрибутам снаружи

❌ Неправильно (например, в мапперы или use-case):

```python
user._security.is_email_verified
```

✅ Правильно:

```python
user.is_email_verified
```

Если нужного property нет — добавьте его в `User`, а не обходите
инкапсуляцию через `_identity`/`_security` напрямую.

## 4. Домен должен быть строгим

Лучше ошибка здесь, чем в базе данных