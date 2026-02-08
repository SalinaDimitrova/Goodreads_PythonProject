from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..models import Collection, Book, User
from ..schemas import CollectionOut, CollectionCreate

api = APIRouter(
    prefix="/collections",
    tags=["collections"],
)

@api.get(
    "/",
    response_model=List[CollectionOut],
    status_code=status.HTTP_200_OK,
)
def get_my_collections(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> List[Collection]:
    return db.query(Collection).filter(
        Collection.user_id == user.id,
    ).all()


@api.post(
    "/",
    response_model=CollectionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_collection(
    data: CollectionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Collection:
    collection: Collection = Collection(
        name=data.name,
        is_default=False,
        user_id=user.id,
    )

    db.add(collection)
    db.commit()
    db.refresh(collection)
    return collection


@api.delete(
    "/{collection_id}",
    status_code=status.HTTP_200_OK,
)
def delete_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    collection: Collection | None = db.get(Collection, collection_id)

    if not collection or collection.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found",
        )

    if collection.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Default collections cannot be deleted",
        )

    db.delete(collection)
    db.commit()
    return {"msg": "Collection deleted"}


@api.post(
    "/{collection_id}/books/{book_id}",
    status_code=status.HTTP_200_OK,
)
def add_book_to_collection(
    collection_id: int,
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    collection: Collection | None = db.get(Collection, collection_id)
    book: Book | None = db.get(Book, book_id)

    if not collection or not book or collection.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    # ако е default → махаме книгата от другите default колекции
    if collection.is_default:
        defaults: List[Collection] = db.query(Collection).filter(
            Collection.user_id == user.id,
            Collection.is_default.is_(True),
        ).all()

        for c in defaults:
            if book in c.books:
                c.books.remove(book)

    if book not in collection.books:
        collection.books.append(book)

    db.commit()
    return {"msg": "Book added to collection"}


@api.delete(
    "/{collection_id}/books/{book_id}",
    status_code=status.HTTP_200_OK,
)
def remove_book_from_collection(
    collection_id: int,
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    collection: Collection | None = db.get(Collection, collection_id)
    book: Book | None = db.get(Book, book_id)

    if not collection or not book or collection.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    if book in collection.books:
        collection.books.remove(book)
        db.commit()

    return {"msg": "Book removed"}
