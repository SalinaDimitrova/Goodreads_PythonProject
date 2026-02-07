from typing import Set, Tuple, List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..models import (
    Book,
    Review,
    Collection,
    FriendRequest,
    FriendStatus,
    User,
)
from ..schemas import BookOut

api = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
)


def get_excluded_book_ids(db: Session, user: User) -> Set[int]:
    excluded: Set[int] = set()

    collections: List[Collection] = db.query(Collection).filter(
        Collection.user_id == user.id,
        Collection.is_default.is_(True),
    ).all()

    for collection in collections:
        if collection.name in ("Reading", "Read"):
            for book in collection.books:
                excluded.add(book.id)

    return excluded


def get_genre_preferences(
    db: Session,
    user: User,
) -> Tuple[Set[int], Set[int]]:
    genre_scores: dict[int, List[int]] = {}

    reviews: List[Review] = db.query(Review).filter(
        Review.user_id == user.id,
    ).all()

    for review in reviews:
        for genre in review.book.genres:
            genre_scores.setdefault(genre.id, []).append(review.rating)

    avg_scores: dict[int, float] = {
        gid: sum(ratings) / len(ratings)
        for gid, ratings in genre_scores.items()
    }

    liked: Set[int] = {
        gid for gid, score in avg_scores.items() if score >= 4
    }
    disliked: Set[int] = {
        gid for gid, score in avg_scores.items() if score <= 2
    }

    return liked, disliked


def books_liked_by_friends(
    db: Session,
    user: User,
) -> List[Book]:
    friend_ids: List[int] = []

    friendships: List[FriendRequest] = db.query(FriendRequest).filter(
        FriendRequest.status == FriendStatus.accepted,
        ((FriendRequest.sender_id == user.id) |
         (FriendRequest.receiver_id == user.id)),
    ).all()

    for fr in friendships:
        friend_ids.append(
            fr.receiver_id if fr.sender_id == user.id else fr.sender_id
        )

    if not friend_ids:
        return []

    return db.query(Book).join(Review).filter(
        Review.user_id.in_(friend_ids),
        Review.rating >= 4,
    ).all()


@api.get(
    "/",
    response_model=List[BookOut],
    status_code=status.HTTP_200_OK,
)
def recommend_books(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> List[Book]:
    excluded: Set[int] = get_excluded_book_ids(db, user)
    liked_genres, disliked_genres = get_genre_preferences(db, user)

    candidates: List[Book] = db.query(Book).filter(
        Book.id.notin_(excluded),
    ).all()

    scored: List[Tuple[float, Book]] = []

    for book in candidates:
        score: float = 0.0

        if book.avg_rating is not None:
            score += book.avg_rating

        genre_ids: Set[int] = {genre.id for genre in book.genres}

        if genre_ids & liked_genres:
            score += 2

        if genre_ids & disliked_genres:
            score -= 2

        scored.append((score, book))

    friend_books: List[Book] = books_liked_by_friends(db, user)
    for book in friend_books:
        scored.append((5.0, book))

    unique: dict[int, Tuple[float, Book]] = {
        book.id: (score, book) for score, book in scored
    }

    result: List[Tuple[float, Book]] = sorted(
        unique.values(),
        key=lambda x: x[0],
        reverse=True,
    )

    return [book for _, book in result[:5]]
