from datetime import datetime, timedelta
from typing import Any, Dict

from jose import jwt

SECRET_KEY: str = "super-secret-key"
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

def create_access_token(data: Dict[str, Any]) -> str:
    """
    Creates a JWT access token.

    :param data: Payload data (must include 'sub')
    :return: Encoded JWT token
    """
    to_encode: Dict[str, Any] = data.copy()

    expire: datetime = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode["exp"] = expire

    encoded_jwt: str = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decodes a JWT token.

    :param token: JWT token string
    :return: Decoded payload
    :raises JWTError: if token is invalid or expired
    """
    payload: Dict[str, Any] = jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )
    return payload
