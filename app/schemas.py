from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ======================
# Users & Auth
# ======================

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"

    @field_validator("password")
    @classmethod
    def password_length(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes")
        return value


class UserOut(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ======================
# Genres & Books
# ======================

class GenreOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class BookCreate(BaseModel):
    title: str
    description: Optional[str] = None
    genre_ids: List[int] = Field(default_factory=list)


class BookOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    author_id: int
    avg_rating: Optional[float]
    genres: List[GenreOut]

    class Config:
        from_attributes = True


# ======================
# Reviews
# ======================

class ReviewCreate(BaseModel):
    rating: int
    comment: Optional[str] = None


class ReviewOut(BaseModel):
    id: int
    rating: int
    comment: Optional[str]
    user_id: int

    class Config:
        from_attributes = True


# ======================
# Collections
# ======================

class CollectionCreate(BaseModel):
    name: str


class CollectionOut(BaseModel):
    id: int
    name: str
    is_default: bool
    books: List[BookOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ======================
# Tags
# ======================

class TagCreate(BaseModel):
    name: str


class TagOut(BaseModel):
    id: int
    name: str
    book_id: int

    class Config:
        from_attributes = True


# ======================
# Friends
# ======================

class FriendRequestOut(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    status: str

    class Config:
        from_attributes = True
