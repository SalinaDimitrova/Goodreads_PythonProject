from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..models import User, Collection
from ..schemas import UserCreate, UserOut

api = APIRouter(
    prefix="/users",
    tags=["users"],
)


@api.post(
    "/",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
) -> User:
    db_user: User = User(
        username=user.username,
        role=user.role,
    )
    db_user.set_password(user.password)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    default_collections: List[str] = ["To Read", "Reading", "Read"]
    for name in default_collections:
        collection: Collection = Collection(
            name=name,
            is_default=True,
            user_id=db_user.id,
        )
        db.add(collection)

    db.commit()
    return db_user


@api.get(
    "/me",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
)
def read_me(
    current_user: User = Depends(get_current_user),
) -> User:
    return current_user
