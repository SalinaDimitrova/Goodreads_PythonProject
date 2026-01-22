# app/api/books.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
#Оправи книгите да не могат да се дублират

from ..deps import get_db, get_current_user
from ..models import Book, Genre, User, Review
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
):
    if user.role not in ["author", "admin"]:
        raise HTTPException(403, "Only authors can add books")

    genres = db.query(Genre).filter(Genre.id.in_(data.genre_ids)).all()

    if len(genres) != len(data.genre_ids):
        raise HTTPException(400, "Invalid genre id")

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
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(404, "Book not found")
    return book

@api.get("/", response_model=List[BookOut])
def search_books(
    title: str = "",
    db: Session = Depends(get_db)
):
    return db.query(Book).filter(Book.title.contains(title)).all()

@api.get("/by-genre/{genre_id}", response_model=List[BookOut])
def books_by_genre(
    genre_id: int,
    db: Session = Depends(get_db)
):
    genre = db.get(Genre, genre_id)
    if not genre:
        raise HTTPException(404, "Genre not found")
    return genre.books

def calculate_avg_rating(book: Book):
    if not book.reviews:
        return None
    return sum(r.rating for r in book.reviews) / len(book.reviews)
