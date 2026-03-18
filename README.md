# CRM Database Project

Проект CRM системи з базою даних PostgreSQL для управління користувачами, дзвінками та аналітикою.

## Структура проекту

```
CRM_Database/
├── alembic/              # Міграції бази даних
│   ├── versions/         # Файли міграцій
│   └── env.py           # Конфігурація Alembic
├── db/                   # Модулі бази даних
│   ├── database.py      # Підключення до БД
│   └── models.py        # SQLAlchemy моделі
├── src/                  # Вихідний код додатку
├── .env                  # Змінні середовища
├── alembic.ini          # Конфігурація Alembic
├── docker-compose.yml   # Docker конфігурація
└── requirements.txt     # Python залежності
```

## Моделі бази даних

- **User** - користувачі системи
- **UserCategory** - категорії користувачів (OneToOne з User)
- **UserType** - типи користувачів (ManyToMany з User)
- **Call** - дзвінки (OneToMany з User)
- **CallAiAnalytic** - AI аналітика дзвінків

## Швидкий старт

### 1. Встановлення залежностей

```bash
pip install -r requirements.txt
```

### 2. Запуск PostgreSQL через Docker

```bash
docker-compose up -d postgres
```

Це запустить:
- **PostgreSQL** на порту `5436`
- **pgAdmin** на порту `5050` (опціонально, для веб-управління БД)

### 3. Перевірка статусу контейнерів

```bash
docker-compose ps
```

### 4. Створення міграцій

```bash
# Створити нову міграцію
alembic revision --autogenerate -m "Initial migration"

# Застосувати міграції
alembic upgrade head
```

### 5. Підключення до pgAdmin (опціонально)

Відкрийте браузер: http://localhost:5050

- Email: `admin@admin.com`
- Password: `admin`

Додайте новий сервер:
- Host: `postgres` (або `localhost` якщо підключаєтесь ззовні Docker)
- Port: `5432` (всередині Docker) або `5436` (ззовні)
- Username: `db_user`
- Password: `db_password`
- Database: `db`

## Корисні команди

### Docker

```bash
# Запустити всі сервіси
docker-compose up -d

# Зупинити всі сервіси
docker-compose down

# Переглянути логи
docker-compose logs -f postgres

# Перезапустити PostgreSQL
docker-compose restart postgres

# Видалити всі дані (включно з БД)
docker-compose down -v
```

### Alembic

```bash
# Переглянути поточну версію БД
alembic current

# Переглянути історію міграцій
alembic history

# Відкотити останню міграцію
alembic downgrade -1

# Застосувати всі міграції
alembic upgrade head
```

### Пряме підключення до PostgreSQL

```bash
# Через Docker
docker exec -it crm_postgres psql -U db_user -d db

# Через psql (якщо встановлено локально)
psql -h localhost -p 5436 -U db_user -d db
```

## Змінні середовища

Файл `.env` містить:

```env
DATABASE_URL=postgresql+asyncpg://db_user:db_password@localhost:5436/db
```

- **asyncpg** - для асинхронної роботи з БД в додатку
- **psycopg2** - використовується Alembic для міграцій (в alembic.ini)

## Налаштування

### Зміна паролів та портів

Відредагуйте `docker-compose.yml`:

```yaml
environment:
  POSTGRES_USER: your_user
  POSTGRES_PASSWORD: your_password
  POSTGRES_DB: your_db
ports:
  - "your_port:5432"
```

Не забудьте оновити `.env` та `alembic.ini` відповідно!

## Troubleshooting

### Порт вже зайнятий

Якщо порт 5436 зайнятий, змініть в `docker-compose.yml`:

```yaml
ports:
  - "5437:5432"  # Використовуйте інший порт
```

### Помилка підключення

Переконайтесь що:
1. Docker контейнер запущений: `docker-compose ps`
2. PostgreSQL готовий приймати підключення: `docker-compose logs postgres`
3. Правильні креденшали в `.env` та `alembic.ini`

### Скидання бази даних

```bash
docker-compose down -v
docker-compose up -d postgres
alembic upgrade head
```
