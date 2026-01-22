# app/api/genres.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
#ОПРАВИ СИ ЖАНРОВЕТЕ ДА НЕ СЕ СЪЗДАВА КНИГА БЕЗ ЖАНР

from ..deps import get_db, get_current_user
from ..models import Genre, User
from ..schemas import GenreOut

api = APIRouter(
    prefix="/genres",
    tags=["Genres"]
)

@api.post("/", response_model=GenreOut)
def create_genre(
    name: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user.role not in ["admin", "author"]:
        raise HTTPException(403, "Not allowed")

    existing = db.query(Genre).filter(Genre.name == name).first()
    if existing:
        raise HTTPException(400, "Genre already exists")

    genre = Genre(name=name)
    db.add(genre)
    db.commit()
    db.refresh(genre)
    return genre


@api.get("/", response_model=list[GenreOut])
def list_genres(db: Session = Depends(get_db)):
    return db.query(Genre).all()


@api.get("/{genre_id}", response_model=GenreOut)
def get_genre(genre_id: int, db: Session = Depends(get_db)):
    genre = db.get(Genre, genre_id)
    if not genre:
        raise HTTPException(404, "Genre not found")
    return genre
