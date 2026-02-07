# app/api/genres.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

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
) -> Genre:
    if user.role not in ["admin", "author"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    existing: Optional[Genre] = db.query(Genre).filter(
        Genre.name == name
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Genre already exists"
        )

    genre = Genre(name=name)
    db.add(genre)
    db.commit()
    db.refresh(genre)
    return genre


@api.get("/", response_model=List[GenreOut])
def list_genres(
    db: Session = Depends(get_db)
) -> List[Genre]:
    return db.query(Genre).all()


@api.get("/{genre_id}", response_model=GenreOut)
def get_genre(
    genre_id: int,
    db: Session = Depends(get_db)
) -> Genre:
    genre: Optional[Genre] = db.get(Genre, genre_id)
    if not genre:
        raise HTTPException(
            status_code=404,
            detail="Genre not found"
        )
    return genre
