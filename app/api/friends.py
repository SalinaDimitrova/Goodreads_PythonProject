from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_db, get_current_user
from ..models import User, FriendRequest, FriendStatus
from ..schemas import FriendRequestOut, UserOut

api = APIRouter(
    prefix="/friends",
    tags=["friends"],
)


@api.post(
    "/{user_id}",
    response_model=FriendRequestOut,
    status_code=status.HTTP_201_CREATED,
)
def send_friend_request(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FriendRequest:
    if user_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add yourself",
        )

    target: User | None = db.get(User, user_id)
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    existing: FriendRequest | None = db.query(FriendRequest).filter(
        ((FriendRequest.sender_id == user.id) &
         (FriendRequest.receiver_id == user_id)) |
        ((FriendRequest.sender_id == user_id) &
         (FriendRequest.receiver_id == user.id))
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request already exists",
        )

    fr: FriendRequest = FriendRequest(
        sender_id=user.id,
        receiver_id=user_id,
    )

    db.add(fr)
    db.commit()
    db.refresh(fr)
    return fr


@api.get(
    "/requests",
    response_model=List[FriendRequestOut],
    status_code=status.HTTP_200_OK,
)
def incoming_requests(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> List[FriendRequest]:
    return db.query(FriendRequest).filter(
        FriendRequest.receiver_id == user.id,
        FriendRequest.status == FriendStatus.pending,
    ).all()


@api.post(
    "/requests/{request_id}/accept",
    status_code=status.HTTP_200_OK,
)
def accept_request(
    request_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    fr: FriendRequest | None = db.get(FriendRequest, request_id)

    if not fr or fr.receiver_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )

    fr.status = FriendStatus.accepted
    db.commit()
    return {"msg": "Friend request accepted"}


@api.post(
    "/requests/{request_id}/reject",
    status_code=status.HTTP_200_OK,
)
def reject_request(
    request_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    fr: FriendRequest | None = db.get(FriendRequest, request_id)

    if not fr or fr.receiver_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )

    fr.status = FriendStatus.rejected
    db.commit()
    return {"msg": "Friend request rejected"}


@api.get(
    "/",
    response_model=List[UserOut],
    status_code=status.HTTP_200_OK,
)
def list_friends(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> List[User]:
    accepted: List[FriendRequest] = db.query(FriendRequest).filter(
        FriendRequest.status == FriendStatus.accepted,
        ((FriendRequest.sender_id == user.id) |
         (FriendRequest.receiver_id == user.id)),
    ).all()

    friends: List[User] = []

    for fr in accepted:
        friend_id: int = (
            fr.receiver_id if fr.sender_id == user.id else fr.sender_id
        )
        friend: User | None = db.get(User, friend_id)
        if friend:
            friends.append(friend)

    return friends


@api.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
)
def remove_friend(
    user_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    fr: FriendRequest | None = db.query(FriendRequest).filter(
        FriendRequest.status == FriendStatus.accepted,
        ((FriendRequest.sender_id == user.id) &
         (FriendRequest.receiver_id == user_id)) |
        ((FriendRequest.sender_id == user_id) &
         (FriendRequest.receiver_id == user.id)),
    ).first()

    if not fr:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Friend not found",
        )

    db.delete(fr)
    db.commit()
    return {"msg": "Friend removed"}
