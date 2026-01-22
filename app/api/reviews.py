from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..deps import get_db, get_current_user
from ..models import Review, Book, User
from ..schemas import ReviewCreate, ReviewOut
#validation of rating 1-5

api = APIRouter(
    prefix="/reviews",
    tags=["Reviews"]
)

@api.post("/books/{book_id}", response_model=ReviewOut)
def add_review(
    book_id: int,
    data: ReviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    book = db.get(Book, book_id)
    if not book:
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

@api.put("/{review_id}", response_model=ReviewOut)
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

@api.delete("/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(404, "Review not found")

    book = db.get(Book, review.book_id)

    if (
        user.id != review.user_id
        and user.id != book.author_id
        and user.role != "admin"
    ):
        raise HTTPException(403, "Not allowed")

    db.delete(review)
    db.commit()
    return {"msg": "Review deleted"}

@api.get("/books/{book_id}", response_model=List[ReviewOut])
def get_book_reviews(
    book_id: int,
    db: Session = Depends(get_db)
):
    return db.query(Review).filter(
        Review.book_id == book_id
    ).all()
