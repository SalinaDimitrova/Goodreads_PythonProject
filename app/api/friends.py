from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..deps import get_db, get_current_user
from ..models import User, FriendRequest, FriendStatus
from ..schemas import FriendRequestOut

api = APIRouter(
    prefix="/friends",
    tags=["Friends"]
)

@api.post("/{user_id}", response_model=FriendRequestOut)
def send_friend_request(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    if user_id == user.id:
        raise HTTPException(400, "Cannot add yourself")

    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found")

    existing = db.query(FriendRequest).filter(
        ((FriendRequest.sender_id == user.id) &
         (FriendRequest.receiver_id == user_id)) |
        ((FriendRequest.sender_id == user_id) &
         (FriendRequest.receiver_id == user.id))
    ).first()

    if existing:
        raise HTTPException(400, "Request already exists")

    fr = FriendRequest(
        sender_id=user.id,
        receiver_id=user_id
    )

    db.add(fr)
    db.commit()
    db.refresh(fr)
    return fr

@api.get("/requests", response_model=List[FriendRequestOut])
def incoming_requests(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    return db.query(FriendRequest).filter(
        FriendRequest.receiver_id == user.id,
        FriendRequest.status == FriendStatus.pending
    ).all()

@api.post("/requests/{request_id}/accept")
def accept_request(
    request_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    fr = db.get(FriendRequest, request_id)

    if not fr or fr.receiver_id != user.id:
        raise HTTPException(404, "Request not found")

    fr.status = FriendStatus.accepted
    db.commit()
    return {"msg": "Friend request accepted"}

@api.post("/requests/{request_id}/reject")
def reject_request(
    request_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    fr = db.get(FriendRequest, request_id)

    if not fr or fr.receiver_id != user.id:
        raise HTTPException(404, "Request not found")

    fr.status = FriendStatus.rejected
    db.commit()
    return {"msg": "Friend request rejected"}

@api.get("/")
def list_friends(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    accepted = db.query(FriendRequest).filter(
        FriendRequest.status == FriendStatus.accepted,
        ((FriendRequest.sender_id == user.id) |
         (FriendRequest.receiver_id == user.id))
    ).all()

    friends = []
    for fr in accepted:
        friend_id = fr.receiver_id if fr.sender_id == user.id else fr.sender_id
        friends.append(db.get(User, friend_id))

    return friends

@api.delete("/{user_id}")
def remove_friend(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    fr = db.query(FriendRequest).filter(
        FriendRequest.status == FriendStatus.accepted,
        ((FriendRequest.sender_id == user.id) &
         (FriendRequest.receiver_id == user_id)) |
        ((FriendRequest.sender_id == user_id) &
         (FriendRequest.receiver_id == user.id))
    ).first()

    if not fr:
        raise HTTPException(404, "Friend not found")

    db.delete(fr)
    db.commit()
    return {"msg": "Friend removed"}
