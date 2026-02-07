# app/api/books.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from ..deps import get_db, get_current_user
from ..models import Book, Genre, User
from ..schemas import BookCreate, BookOut

api = APIRouter(
    prefix="/books",
    tags=["Books"]
)


@api.post("/", response_model=BookOut)
def create_book(
    data: BookCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
) -> Book:
    # ❗ книга БЕЗ жанр – забранено
    if not data.genre_ids:
        raise HTTPException(
            status_code=400,
            detail="A book must have at least one genre"
        )
    # само author / admin
    if user.role not in ["author", "admin"]:
        raise HTTPException(status_code=403, detail="Only authors can add books")

    # 🔴 проверка за дубликат
    existing: Optional[Book] = db.query(Book).filter(
        Book.title == data.title,
        Book.author_id == user.id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="You already have a book with this title"
        )

    # валидиране на жанровете
    genres: List[Genre] = db.query(Genre).filter(
        Genre.id.in_(data.genre_ids)
    ).all()

    if len(genres) != len(data.genre_ids):
        raise HTTPException(status_code=400, detail="Invalid genre id")

    book = Book(
        title=data.title,
        description=data.description,
        author_id=user.id,
        genres=genres
    )

    db.add(book)
    db.commit()
    db.refresh(book)
    return book


@api.get("/{book_id}", response_model=BookOut)
def get_book(
    book_id: int,
    db: Session = Depends(get_db)
) -> Book:
    book: Optional[Book] = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@api.get("/", response_model=List[BookOut])
def search_books(
    title: str = "",
    db: Session = Depends(get_db)
) -> List[Book]:
    return db.query(Book).filter(
        Book.title.contains(title)
    ).all()


@api.get("/by-genre/{genre_id}", response_model=List[BookOut])
def books_by_genre(
    genre_id: int,
    db: Session = Depends(get_db)
) -> List[Book]:
    genre: Optional[Genre] = db.get(Genre, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    return genre.books
