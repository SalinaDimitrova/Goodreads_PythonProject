from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .database import Base, engine
from .models import User, Book, Genre, Review, Collection, Tag, FriendRequest, FriendStatus
from .schemas import UserCreate, UserOut, BookCreate, BookOut, GenreOut, ReviewCreate, ReviewOut, CollectionOut, \
    CollectionCreate, TagCreate, TagOut, FriendRequestOut, LoginRequest, TokenOut
from .deps import get_db, get_current_user
from .auth import create_access_token
from fastapi.security import OAuth2PasswordRequestForm

from .db_init import init_db
init_db()


app = FastAPI(title="Goodreads for X")

@app.post("/users", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(
        username=user.username,
        role=user.role
    )
    db_user.set_password(user.password)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # default collections
    for name in ["To Read", "Reading", "Read"]:
        db.add(Collection(
            name=name,
            is_default=True,
            user_id=db_user.id
        ))
    db.commit()

    return db_user

@app.post("/login", response_model=TokenOut)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not user.verify_password(form_data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": str(user.id),
        "role": user.role
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }


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

@app.post("/books/{book_id}/tags", response_model=TagOut)
def add_tag(
    book_id: int,
    data: TagCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(404, "Book not found")

    # не допускаме дублиране на същия таг за същата книга от същия user
    existing = db.query(Tag).filter(
        Tag.book_id == book_id,
        Tag.user_id == user.id,
        Tag.name == data.name
    ).first()

    if existing:
        raise HTTPException(400, "Tag already exists")

    tag = Tag(
        name=data.name,
        user_id=user.id,
        book_id=book_id
    )

    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

@app.delete("/tags/{tag_id}")
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    tag = db.get(Tag, tag_id)

    if not tag or tag.user_id != user.id:
        raise HTTPException(404, "Tag not found")

    db.delete(tag)
    db.commit()
    return {"msg": "Tag deleted"}

@app.get("/tags/{tag_name}/books", response_model=list[BookOut])
def books_by_tag(
    tag_name: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    tags = db.query(Tag).filter(
        Tag.name == tag_name,
        Tag.user_id == user.id
    ).all()

    return [tag.book for tag in tags]

@app.get("/books/{book_id}/tags", response_model=list[TagOut])
def get_my_tags_for_book(
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return db.query(Tag).filter(
        Tag.book_id == book_id,
        Tag.user_id == user.id
    ).all()

@app.post("/friends/{user_id}", response_model=FriendRequestOut)
def send_friend_request(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user_id == user.id:
        raise HTTPException(400, "Cannot add yourself")

    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found")

    existing = db.query(FriendRequest).filter(
        ((FriendRequest.sender_id == user.id) &
         (FriendRequest.receiver_id == user_id)) |
        ((FriendRequest.sender_id == user_id) &
         (FriendRequest.receiver_id == user.id))
    ).first()

    if existing:
        raise HTTPException(400, "Request already exists")

    fr = FriendRequest(
        sender_id=user.id,
        receiver_id=user_id
    )

    db.add(fr)
    db.commit()
    db.refresh(fr)
    return fr

@app.get("/friends/requests", response_model=list[FriendRequestOut])
def incoming_requests(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return db.query(FriendRequest).filter(
        FriendRequest.receiver_id == user.id,
        FriendRequest.status == FriendStatus.pending
    ).all()

@app.post("/friends/requests/{request_id}/accept")
def accept_request(
    request_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    fr = db.get(FriendRequest, request_id)

    if not fr or fr.receiver_id != user.id:
        raise HTTPException(404, "Request not found")

    fr.status = FriendStatus.accepted
    db.commit()
    return {"msg": "Friend request accepted"}

@app.post("/friends/requests/{request_id}/reject")
def reject_request(
    request_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    fr = db.get(FriendRequest, request_id)

    if not fr or fr.receiver_id != user.id:
        raise HTTPException(404, "Request not found")

    fr.status = FriendStatus.rejected
    db.commit()
    return {"msg": "Friend request rejected"}

@app.get("/friends")
def list_friends(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    accepted = db.query(FriendRequest).filter(
        FriendRequest.status == FriendStatus.accepted,
        ((FriendRequest.sender_id == user.id) |
         (FriendRequest.receiver_id == user.id))
    ).all()

    friends = []
    for fr in accepted:
        friend_id = fr.receiver_id if fr.sender_id == user.id else fr.sender_id
        friends.append(db.get(User, friend_id))

    return friends

@app.delete("/friends/{user_id}")
def remove_friend(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    fr = db.query(FriendRequest).filter(
        FriendRequest.status == FriendStatus.accepted,
        ((FriendRequest.sender_id == user.id) &
         (FriendRequest.receiver_id == user_id)) |
        ((FriendRequest.sender_id == user_id) &
         (FriendRequest.receiver_id == user.id))
    ).first()

    if not fr:
        raise HTTPException(404, "Friend not found")

    db.delete(fr)
    db.commit()
    return {"msg": "Friend removed"}

def get_excluded_book_ids(db: Session, user: User):
    from .models import Collection

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

    reviews = db.query(Review).filter(Review.user_id == user.id).all()

    for r in reviews:
        for g in r.book.genres:
            genre_scores.setdefault(g.id, []).append(r.rating)

    avg = {gid: sum(v)/len(v) for gid, v in genre_scores.items()}

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
        friend_ids.append(fr.receiver_id if fr.sender_id == user.id else fr.sender_id)

    return db.query(Book).join(Review).filter(
        Review.user_id.in_(friend_ids),
        Review.rating >= 4
    ).all()

@app.get("/recommendations")
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

    # махаме дубликати
    unique = {b.id: (s, b) for s, b in scored}

    result = sorted(unique.values(), key=lambda x: x[0], reverse=True)

    return [b for _, b in result[:5]]
