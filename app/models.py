from sqlalchemy import Column, Integer, String, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
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


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    cover_url = Column(String)

    author_id = Column(Integer, ForeignKey("users.id"))
    author = relationship("User")

    genres = relationship("Genre", secondary=book_genres, back_populates="books")


class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    books = relationship("Book", secondary=book_genres, back_populates="genres")
