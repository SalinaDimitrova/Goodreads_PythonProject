from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..deps import get_db, get_current_user
from ..models import Collection, Book, User
from ..schemas import CollectionOut, CollectionCreate

api = APIRouter(
    prefix="/collections",
    tags=["Collections"]
)

@api.get("/", response_model=List[CollectionOut])
def get_my_collections(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return db.query(Collection).filter(
        Collection.user_id == user.id
    ).all()

@api.post("/", response_model=CollectionOut)
def create_collection(
    data: CollectionCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    collection = Collection(
        name=data.name,
        is_default=False,
        user_id=user.id
    )

    db.add(collection)
    db.commit()
    db.refresh(collection)
    return collection

@api.delete("/{collection_id}")
def delete_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    collection = db.get(Collection, collection_id)

    if not collection or collection.user_id != user.id:
        raise HTTPException(404, "Collection not found")

    if collection.is_default:
        raise HTTPException(400, "Default collections cannot be deleted")

    db.delete(collection)
    db.commit()
    return {"msg": "Collection deleted"}

@api.post("/{collection_id}/books/{book_id}")
def add_book_to_collection(
    collection_id: int,
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    collection = db.get(Collection, collection_id)
    book = db.get(Book, book_id)

    if not collection or not book or collection.user_id != user.id:
        raise HTTPException(404, "Not found")

    # ако е default → махаме от другите default
    if collection.is_default:
        defaults = db.query(Collection).filter(
            Collection.user_id == user.id,
            Collection.is_default == True
        ).all()

        for c in defaults:
            if book in c.books:
                c.books.remove(book)

    if book not in collection.books:
        collection.books.append(book)

    db.commit()
    return {"msg": "Book added to collection"}

@api.delete("/{collection_id}/books/{book_id}")
def remove_book_from_collection(
    collection_id: int,
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    collection = db.get(Collection, collection_id)
    book = db.get(Book, book_id)

    if not collection or not book or collection.user_id != user.id:
        raise HTTPException(404, "Not found")

    if book in collection.books:
        collection.books.remove(book)
        db.commit()

    return {"msg": "Book removed"}
