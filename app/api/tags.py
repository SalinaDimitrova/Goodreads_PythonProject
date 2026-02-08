from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..models import Tag, Book, User
from ..schemas import TagCreate, TagOut, BookOut

api = APIRouter(
    prefix="/tags",
    tags=["tags"],
)

@api.post(
    "/books/{book_id}",
    response_model=TagOut,
    status_code=status.HTTP_201_CREATED,
)
def add_tag(
    book_id: int,
    data: TagCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Tag:
    book: Book | None = db.get(Book, book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )

    tag_name: str = data.name.strip().lower()

    existing: Tag | None = db.query(Tag).filter(
        Tag.book_id == book_id,
        Tag.user_id == user.id,
        Tag.name == tag_name,
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag already exists",
        )

    tag: Tag = Tag(
        name=tag_name,
        user_id=user.id,
        book_id=book_id,
    )

    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag

@api.delete(
    "/{tag_id}",
    status_code=status.HTTP_200_OK,
)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    tag: Tag | None = db.get(Tag, tag_id)

    if not tag or tag.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    db.delete(tag)
    db.commit()
    return {"msg": "Tag deleted"}

@api.get(
    "/{tag_name}/books",
    response_model=List[BookOut],
    status_code=status.HTTP_200_OK,
)
def books_by_tag(
    tag_name: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> List[Book]:
    tags: List[Tag] = db.query(Tag).filter(
        Tag.name == tag_name.lower(),
        Tag.user_id == user.id,
    ).all()

    return [tag.book for tag in tags]

@api.get(
    "/books/{book_id}",
    response_model=List[TagOut],
    status_code=status.HTTP_200_OK,
)
def get_my_tags_for_book(
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> List[Tag]:
    return db.query(Tag).filter(
        Tag.book_id == book_id,
        Tag.user_id == user.id,
    ).all()
