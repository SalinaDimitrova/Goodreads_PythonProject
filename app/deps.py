from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from .database import SessionLocal
from .models import User

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db),
    x_user_id: int = Header(...)
):
    user = db.query(User).get(x_user_id)
    if not user:
        raise HTTPException(401, "Invalid user")
    return user
