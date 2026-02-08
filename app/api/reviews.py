from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..models import Review, Book, User
from ..schemas import ReviewCreate, ReviewOut

api = APIRouter(
    prefix="/reviews",
    tags=["reviews"],
)

def validate_rating(rating: int) -> None:
    if rating < 1 or rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rating must be between 1 and 5",
        )

@api.post(
    "/books/{book_id}",
    response_model=ReviewOut,
    status_code=status.HTTP_201_CREATED,
)
def add_review(
    book_id: int,
    data: ReviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Review:
    validate_rating(data.rating)

    book: Book | None = db.get(Book, book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    existing: Review | None = db.query(Review).filter(
        Review.book_id == book_id,
        Review.user_id == user.id,
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already reviewed this book",
        )

    review: Review = Review(
        rating=data.rating,
        comment=data.comment,
        user_id=user.id,
        book_id=book_id,
    )

    db.add(review)
    db.commit()
    db.refresh(review)
    return review

@api.put(
    "/{review_id}",
    response_model=ReviewOut,
    status_code=status.HTTP_200_OK,
)
def edit_review(
    review_id: int,
    data: ReviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Review:
    validate_rating(data.rating)

    review: Review | None = db.get(Review, review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    if review.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your review",
        )

    review.rating = data.rating
    review.comment = data.comment
    db.commit()
    return review

@api.delete(
    "/{review_id}",
    status_code=status.HTTP_200_OK,
)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    review: Review | None = db.get(Review, review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    book: Book | None = db.get(Book, review.book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    if (
        user.id != review.user_id
        and user.id != book.author_id
        and user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed",
        )

    db.delete(review)
    db.commit()
    return {"msg": "Review deleted"}

@api.get(
    "/books/{book_id}",
    response_model=List[ReviewOut],
    status_code=status.HTTP_200_OK,
)
def get_book_reviews(
    book_id: int,
    db: Session = Depends(get_db),
) -> List[Review]:
    return db.query(Review).filter(
        Review.book_id == book_id,
    ).all()
