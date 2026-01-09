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
    description: Optional[str]
    author_id: int
    genres: List[GenreOut]

    class Config:
        orm_mode = True
