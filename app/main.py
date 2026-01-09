from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import Base, engine
from .models import User, Book, Genre
from .schemas import UserCreate, UserOut, BookCreate, BookOut, GenreOut
from .deps import get_db, get_current_user

from typing import List

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Goodreads for X")

@app.post("/users", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(
        username=user.username,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/genres", response_model=GenreOut)
def create_genre(
    name: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.role not in ["admin", "author"]:
        raise HTTPException(403, "Not allowed")

    genre = Genre(name=name)
    db.add(genre)
    db.commit()
    db.refresh(genre)
    return genre

@app.post("/books", response_model=BookOut)
def create_book(
    data: BookCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.role not in ["author", "admin"]:
        raise HTTPException(403, "Only authors can add books")

    genres = db.query(Genre).filter(Genre.id.in_(data.genre_ids)).all()

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

@app.get("/books/{book_id}", response_model=BookOut)
def get_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(404, "Book not found")
    return book

@app.get("/books", response_model=List[BookOut])
def search_books(title: str = "", db: Session = Depends(get_db)):
    return db.query(Book).filter(Book.title.contains(title)).all()

@app.get("/genres/{genre_id}/books", response_model=List[BookOut])
def books_by_genre(genre_id: int, db: Session = Depends(get_db)):
    genre = db.query(Genre).get(genre_id)
    if not genre:
        raise HTTPException(404, "Genre not found")
    return genre.books

