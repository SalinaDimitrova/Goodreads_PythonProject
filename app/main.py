from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import Base, engine
from .models import User, Book, Genre, Review, Collection
from .schemas import UserCreate, UserOut, BookCreate, BookOut, GenreOut, ReviewCreate, ReviewOut, CollectionOut, \
    CollectionCreate
from .deps import get_db, get_current_user

from typing import List

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Goodreads for X")

@app.post("/users", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(username=user.username, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    default_names = ["To Read", "Reading", "Read"]
    for name in default_names:
        db.add(Collection(
            name=name,
            is_default=True,
            user_id=db_user.id
        ))
    db.commit()

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

@app.post("/books/{book_id}/reviews", response_model=ReviewOut)
def add_review(
    book_id: int,
    data: ReviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if not db.get(Book, book_id):
        raise HTTPException(404, "Book not found")

    existing = db.query(Review).filter(
        Review.book_id == book_id,
        Review.user_id == user.id
    ).first()

    if existing:
        raise HTTPException(400, "You already reviewed this book")

    review = Review(
        rating=data.rating,
        comment=data.comment,
        user_id=user.id,
        book_id=book_id
    )

    db.add(review)
    db.commit()
    db.refresh(review)
    return review

@app.put("/reviews/{review_id}", response_model=ReviewOut)
def edit_review(
    review_id: int,
    data: ReviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(404, "Review not found")

    if review.user_id != user.id:
        raise HTTPException(403, "Not your review")

    review.rating = data.rating
    review.comment = data.comment
    db.commit()
    return review

@app.delete("/reviews/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(404, "Review not found")

    book = db.get(Book, review.book_id)

    if user.id != review.user_id and user.id != book.author_id and user.role != "admin":
        raise HTTPException(403, "Not allowed")

    db.delete(review)
    db.commit()
    return {"msg": "Review deleted"}

@app.get("/books/{book_id}/reviews", response_model=List[ReviewOut])
def get_book_reviews(book_id: int, db: Session = Depends(get_db)):
    return db.query(Review).filter(Review.book_id == book_id).all()

@app.get("/collections", response_model=list[CollectionOut])
def get_my_collections(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return db.query(Collection).filter(Collection.user_id == user.id).all()

@app.post("/collections", response_model=CollectionOut)
def create_collection(
    data: CollectionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    collection = Collection(
        name=data.name,
        is_default=False,
        user_id=user.id
    )
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return collection

@app.delete("/collections/{collection_id}")
def delete_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    collection = db.get(Collection, collection_id)

    if not collection or collection.user_id != user.id:
        raise HTTPException(404, "Collection not found")

    if collection.is_default:
        raise HTTPException(400, "Default collections cannot be deleted")

    db.delete(collection)
    db.commit()
    return {"msg": "Collection deleted"}

@app.post("/collections/{collection_id}/books/{book_id}")
def add_book_to_collection(
    collection_id: int,
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    collection = db.get(Collection, collection_id)
    book = db.get(Book, book_id)

    if not collection or not book or collection.user_id != user.id:
        raise HTTPException(404, "Not found")

    # ако е default → махаме от другите default
    if collection.is_default:
        defaults = db.query(Collection).filter(
            Collection.user_id == user.id,
            Collection.is_default == True
        ).all()

        for c in defaults:
            if book in c.books:
                c.books.remove(book)

    if book not in collection.books:
        collection.books.append(book)

    db.commit()
    return {"msg": "Book added to collection"}

@app.delete("/collections/{collection_id}/books/{book_id}")
def remove_book_from_collection(
    collection_id: int,
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    collection = db.get(Collection, collection_id)
    book = db.get(Book, book_id)

    if not collection or not book or collection.user_id != user.id:
        raise HTTPException(404, "Not found")

    if book in collection.books:
        collection.books.remove(book)
        db.commit()

    return {"msg": "Book removed"}
