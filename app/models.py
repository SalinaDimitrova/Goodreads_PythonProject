from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table, CheckConstraint, select, Boolean, Enum
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.sql import func
from .database import Base
import enum

from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

book_genres = Table(
    "book_genres",
    Base.metadata,
    Column("book_id", ForeignKey("books.id"), primary_key=True),
    Column("genre_id", ForeignKey("genres.id"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")

    reviews = relationship(
        "Review",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def set_password(self, password: str):
        password = password.strip()

        if len(password.encode("utf-8")) > 72:
            raise ValueError("Password too long (max 72 bytes)")

        self.password_hash = pwd_context.hash(password)

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)

    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))

    user = relationship("User", back_populates="reviews")
    book = relationship("Book", back_populates="reviews")

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    cover_url = Column(String)

    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User")

    genres = relationship("Genre", secondary=book_genres, back_populates="books")
    reviews = relationship(
        "Review",
        back_populates="book",
        cascade="all, delete-orphan"
    )

    avg_rating = column_property(
        select(func.avg(Review.rating))
        .where(Review.book_id == id)
        .correlate_except(Review)
        .scalar_subquery()
    )

    collections = relationship(
        "Collection",
        secondary="collection_books",
        back_populates="books"
    )


class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    books = relationship("Book", secondary=book_genres, back_populates="genres")

class Collection(Base):
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    is_default = Column(Boolean, default=False)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")

    books = relationship(
        "Book",
        secondary="collection_books",
        back_populates="collections"
    )


collection_books = Table(
    "collection_books",
    Base.metadata,
    Column("collection_id", ForeignKey("collections.id"), primary_key=True),
    Column("book_id", ForeignKey("books.id"), primary_key=True),
)

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))

    user = relationship("User")
    book = relationship("Book")

    __table_args__ = (
        CheckConstraint("length(name) > 0"),
    )

class FriendStatus(enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"

class FriendRequest(Base):
    __tablename__ = "friend_requests"

    id = Column(Integer, primary_key=True)

    sender_id = Column(Integer, ForeignKey("users.id"))
    receiver_id = Column(Integer, ForeignKey("users.id"))

    status = Column(Enum(FriendStatus), default=FriendStatus.pending)

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])