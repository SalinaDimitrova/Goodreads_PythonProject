from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..models import Book, Review, Collection, FriendRequest, FriendStatus, User

api = APIRouter(
    prefix="/recommendations",
    tags=["Recommendations"]
)

def get_excluded_book_ids(db: Session, user: User):
    excluded = set()

    collections = db.query(Collection).filter(
        Collection.user_id == user.id,
        Collection.is_default == True
    ).all()

    for c in collections:
        if c.name in ["Reading", "Read"]:
            for book in c.books:
                excluded.add(book.id)

    return excluded


def get_genre_preferences(db: Session, user: User):
    genre_scores = {}

    reviews = db.query(Review).filter(
        Review.user_id == user.id
    ).all()

    for r in reviews:
        for g in r.book.genres:
            genre_scores.setdefault(g.id, []).append(r.rating)

    avg = {gid: sum(v) / len(v) for gid, v in genre_scores.items()}

    liked = {gid for gid, score in avg.items() if score >= 4}
    disliked = {gid for gid, score in avg.items() if score <= 2}

    return liked, disliked


def books_liked_by_friends(db: Session, user: User):
    friend_ids = []

    friendships = db.query(FriendRequest).filter(
        FriendRequest.status == FriendStatus.accepted,
        ((FriendRequest.sender_id == user.id) |
         (FriendRequest.receiver_id == user.id))
    ).all()

    for fr in friendships:
        friend_ids.append(
            fr.receiver_id if fr.sender_id == user.id else fr.sender_id
        )

    return db.query(Book).join(Review).filter(
        Review.user_id.in_(friend_ids),
        Review.rating >= 4
    ).all()


@api.get("/")
def recommend_books(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    excluded = get_excluded_book_ids(db, user)
    liked_genres, disliked_genres = get_genre_preferences(db, user)

    candidates = db.query(Book).filter(
        Book.id.notin_(excluded)
    ).all()

    scored = []

    for book in candidates:
        score = 0

        if book.avg_rating:
            score += book.avg_rating

        genre_ids = {g.id for g in book.genres}

        if genre_ids & liked_genres:
            score += 2

        if genre_ids & disliked_genres:
            score -= 2

        scored.append((score, book))

    friend_books = books_liked_by_friends(db, user)
    for b in friend_books:
        scored.append((5, b))

    unique = {b.id: (s, b) for s, b in scored}

    result = sorted(
        unique.values(),
        key=lambda x: x[0],
        reverse=True
    )

    return [b for _, b in result[:5]]
