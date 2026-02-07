# Goodreads_X

Backend API проект, вдъхновен от платформата Goodreads, разработен с **FastAPI** и **SQLAlchemy**.  
Проектът позволява управление на книги, потребители, ревюта, колекции, приятелства и препоръки за книги.

---

## 🚀 Технологии

- Python 3.10+
- FastAPI
- SQLAlchemy
- SQLite
- Pytest
- Coverage / pytest-cov
- mypy
- pylint

---

## 📦 Инсталация

1. Клониране / разархивиране на проекта
2. Създаване на виртуална среда (по желание)
3. Инсталиране на зависимостите:

```bash
pip install -r requirements.txt
```

Инсталира всички необходими зависимости за проекта.

---

## ▶️ Стартиране на приложението
```bash
uvicorn app.main:app --reload
```
Стартира FastAPI сървъра в development режим.

API документация:
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/redoc

---

## 🧪 Тестове
```bash
pytest
```
Стартира всички автоматични тестове.

---

## 📊 Coverage
```bash
pytest --cov=app
```

Изчислява тестовото покритие на проекта.  
Проектът има над **80% coverage**.

---

## 🧠 Type hints
```bash
mypy -p app
```
Проверка на type hints с mypy.

---

## 🧹 PEP-8 / pylint
```bash
pylint app
```
Проверка на кода спрямо PEP-8 и pylint правила.

---

## 📁 Структура на проекта

app/  
├── api/ – API endpoints  
├── auth.py – Authentication & JWT  
├── database.py – Database setup  
├── db_init.py – DB initialization  
├── deps.py – Dependencies  
├── models.py – ORM models  
├── schemas.py – Pydantic schemas  
└── main.py – FastAPI entry point  

tests/  
├── conftest.py  
├── test_auth.py  
├── test_books.py  
├── test_collections.py  
├── test_friends.py  
├── test_recommendations.py  
├── test_reviews.py  
└── test_users.py  

---

## 👤 Автор

Учебен проект по Python (FastAPI).