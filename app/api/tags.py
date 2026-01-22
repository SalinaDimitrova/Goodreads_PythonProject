from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..deps import get_db, get_current_user
from ..models import Tag, Book, User
from ..schemas import TagCreate, TagOut

api = APIRouter(
    prefix="/tags",
    tags=["Tags"]
)

@api.post("/books/{book_id}", response_model=TagOut)
def add_tag(
    book_id: int,
    data: TagCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(404, "Book not found")

    existing = db.query(Tag).filter(
        Tag.book_id == book_id,
        Tag.user_id == user.id,
        Tag.name == data.name
    ).first()

    if existing:
        raise HTTPException(400, "Tag already exists")

    tag = Tag(
        name=data.name,
        user_id=user.id,
        book_id=book_id
    )

    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

@api.delete("/{tag_id}")
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    tag = db.get(Tag, tag_id)

    if not tag or tag.user_id != user.id:
        raise HTTPException(404, "Tag not found")

    db.delete(tag)
    db.commit()
    return {"msg": "Tag deleted"}

@api.get("/{tag_name}/books", response_model=List)
def books_by_tag(
    tag_name: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    tags = db.query(Tag).filter(
        Tag.name == tag_name,
        Tag.user_id == user.id
    ).all()

    return [tag.book for tag in tags]

@api.get("/books/{book_id}", response_model=List[TagOut])
def get_my_tags_for_book(
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return db.query(Tag).filter(
        Tag.book_id == book_id,
        Tag.user_id == user.id
    ).all()
