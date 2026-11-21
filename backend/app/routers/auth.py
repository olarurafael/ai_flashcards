from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import User
from app.schemas import Credentials, Token, UserOut
from app.security import AppSettings, CurrentUser, DbSession, create_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(body: Credentials, db: DbSession, settings: AppSettings) -> Token:
    user = User(email=body.email.lower(), password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists") from None
    return Token(access_token=create_token(user.id, settings))


@router.post("/login", response_model=Token)
def login(body: Credentials, db: DbSession, settings: AppSettings) -> Token:
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or user.password_hash is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong email or password")
    return Token(access_token=create_token(user.id, settings))


@router.post("/guest", response_model=Token, status_code=status.HTTP_201_CREATED)
def guest(db: DbSession, settings: AppSettings) -> Token:
    user = User(is_guest=True)
    db.add(user)
    db.commit()
    return Token(access_token=create_token(user.id, settings))


@router.post("/claim", response_model=Token)
def claim_guest(body: Credentials, user: CurrentUser, db: DbSession, settings: AppSettings) -> Token:
    """Turn the current guest into a regular account, keeping its decks."""
    if not user.is_guest:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This account already has an email")
    user.email = body.email.lower()
    user.password_hash = hash_password(body.password)
    user.is_guest = False
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists") from None
    return Token(access_token=create_token(user.id, settings))


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> User:
    return user
