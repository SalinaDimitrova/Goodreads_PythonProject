from pydantic import BaseModel, field_validator
from typing import List, Optional


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"

    @field_validator("password")
    @classmethod
    def password_length(cls, v):
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes")
        return v

class UserOut(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        orm_mode = True

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


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

class TagCreate(BaseModel):
    name: str

class TagOut(BaseModel):
    id: int
    name: str
    book_id: int

    class Config:
        orm_mode = True

class FriendRequestOut(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    status: str

    class Config:
        orm_mode = True