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
├── interfaces/      # Контракты (репозитории)
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

* email → сбрасывает верификацию
* всегда обновляется `updated_at`

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

# 🗂️ Repository Interfaces

## 📌 Назначение

Контракт между:

* application layer
* infrastructure layer

---

## 📚 Методы

```python
async def get_by_id(user_id: UUID) -> User | None
async def get_by_username(username: str) -> User | None
async def get_by_email(email: str) -> User | None

async def create_user(user: User) -> None
async def update_user(user: User) -> None
```

---

## ⚠️ Ограничения

Запрещено:

* использовать ORM
* писать SQL
* добавлять бизнес-логику

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

---

## 2. Не теряйте данные при изменениях

При изменении одного поля:
→ остальные должны сохраняться

---

## 3. Домен должен быть строгим

Лучше ошибка здесь, чем в базе данных

---

