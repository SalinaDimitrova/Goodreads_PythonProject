from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..models import User, Collection
from ..schemas import UserCreate, UserOut

api = APIRouter(prefix="/users", tags=["Users"])

@api.post("/", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(
        username=user.username,
        role=user.role
    )
    db_user.set_password(user.password)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    for name in ["To Read", "Reading", "Read"]:
        db.add(Collection(
            name=name,
            is_default=True,
            user_id=db_user.id
        ))

    db.commit()
    return db_user


@api.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user
