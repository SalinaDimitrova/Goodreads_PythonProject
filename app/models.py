from __future__ import annotations

import enum
from typing import List, Optional

from sqlalchemy import (
    Column,
    String,
    Text,
    ForeignKey,
    Table,
    Boolean,
    Enum,
    CheckConstraint,
    select,
)
from sqlalchemy.orm import relationship, column_property, Mapped, mapped_column
from sqlalchemy.sql import func

from passlib.context import CryptContext

from .database import Base

# ======================
# Password hashing
# ======================

pwd_context: CryptContext = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

# ======================
# Association tables
# ======================

book_genres: Table = Table(
    "book_genres",
    Base.metadata,
    Column("book_id", ForeignKey("books.id"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id"), primary_key=True),
)

collection_books: Table = Table(
    "collection_books",
    Base.metadata,
    Column("collection_id", ForeignKey("collections.id"), primary_key=True),
    Column("book_id", ForeignKey("books.id"), primary_key=True),
)

# ======================
# Models
# ======================


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, default="user")

    reviews: Mapped[List[Review]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    collections: Mapped[List[Collection]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def set_password(self, password: str) -> None:
        password = password.strip()

        if len(password.encode("utf-8")) > 72:
            raise ValueError("Password too long (max 72 bytes)")

        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    rating: Mapped[int] = mapped_column(nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))

    user: Mapped[User] = relationship(back_populates="reviews")
    book: Mapped[Book] = relationship(back_populates="reviews")

class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    cover_url: Mapped[Optional[str]] = mapped_column(String)

    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    author: Mapped[User] = relationship()

    genres: Mapped[List[Genre]] = relationship(
        secondary=book_genres,
        back_populates="books",
    )

    reviews: Mapped[List[Review]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
    )

    collections: Mapped[List[Collection]] = relationship(
        secondary=collection_books,
        back_populates="books",
    )

    avg_rating: Mapped[Optional[float]] = column_property(
        select(func.avg(Review.rating))
        .where(Review.book_id == id)
        .correlate_except(Review)
        .scalar_subquery()
    )


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    books: Mapped[List[Book]] = relationship(
        secondary=book_genres,
        back_populates="genres",
    )


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped[User] = relationship(back_populates="collections")

    books: Mapped[List[Book]] = relationship(
        secondary=collection_books,
        back_populates="collections",
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))

    user: Mapped[User] = relationship()
    book: Mapped[Book] = relationship()

    __table_args__ = (
        CheckConstraint("length(name) > 0"),
    )


class FriendStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id: Mapped[int] = mapped_column(primary_key=True)

    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    receiver_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    status: Mapped[FriendStatus] = mapped_column(
        Enum(FriendStatus),
        default=FriendStatus.pending,
    )

    sender: Mapped[User] = relationship(
        foreign_keys=[sender_id]
    )
    receiver: Mapped[User] = relationship(
        foreign_keys=[receiver_id]
    )
