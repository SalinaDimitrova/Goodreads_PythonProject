from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table, CheckConstraint, select, Boolean
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.sql import func
from .database import Base

# many-to-many таблица
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
    role = Column(String, default="user")  # user | author | admin

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)

    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5"),
    )

    user = relationship("User")
    book = relationship("Book")

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    cover_url = Column(String)

    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User")

    genres = relationship("Genre", secondary=book_genres, back_populates="books")
    reviews = relationship("Review", cascade="all, delete")

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