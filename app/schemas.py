from pydantic import BaseModel
from typing import List, Optional

class UserCreate(BaseModel):
    username: str
    role: str = "user"

class UserOut(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        orm_mode = True

class GenreOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class BookCreate(BaseModel):
    title: str
    description: Optional[str] = None
    genre_ids: List[int] = []


class BookOut(BaseModel):
    id: int
    title: str
    description: str | None
    author_id: int
    avg_rating: float | None
    genres: List[GenreOut]

    class Config:
        orm_mode = True

class ReviewCreate(BaseModel):
    rating: int
    comment: str | None = None

class ReviewOut(BaseModel):
    id: int
    rating: int
    comment: str | None
    user_id: int

    class Config:
        orm_mode = True

class CollectionCreate(BaseModel):
    name: str

class CollectionOut(BaseModel):
    id: int
    name: str
    is_default: bool
    books: list[BookOut] = []

    class Config:
        orm_mode = True
