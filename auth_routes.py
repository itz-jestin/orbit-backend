from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

import auth_models
import auth_schemas
from auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from database import get_db

router = APIRouter()


@router.post("/auth/register", response_model=auth_schemas.TokenResponse)
def register(payload: auth_schemas.RegisterRequest, db: Session = Depends(get_db)):
    existing = (
        db.query(auth_models.User)
        .filter(auth_models.User.email == payload.email)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Email is already registered")

    user = auth_models.User(
        email=payload.email,
        name=payload.name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return auth_schemas.TokenResponse(access_token=token, user=user)


@router.post("/auth/login", response_model=auth_schemas.TokenResponse)
def login(payload: auth_schemas.LoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(auth_models.User)
        .filter(auth_models.User.email == payload.email)
        .first()
    )
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token(user.id)
    return auth_schemas.TokenResponse(access_token=token, user=user)


@router.get("/auth/me", response_model=auth_schemas.UserOut)
def me(current_user: auth_models.User = Depends(get_current_user)):
    return current_user


@router.get("/history", response_model=list[auth_schemas.HistoryListItemOut])
def list_history(
    current_user: auth_models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(auth_models.ResearchHistory)
        .filter(auth_models.ResearchHistory.user_id == current_user.id)
        .order_by(auth_models.ResearchHistory.created_at.desc())
        .all()
    )
    return items


@router.get("/history/{history_id}", response_model=auth_schemas.HistoryItemOut)
def get_history_item(
    history_id: str,
    current_user: auth_models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(auth_models.ResearchHistory)
        .filter(
            auth_models.ResearchHistory.id == history_id,
            auth_models.ResearchHistory.user_id == current_user.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="History item not found")
    return item


@router.delete("/history/{history_id}", status_code=204)
def delete_history_item(
    history_id: str,
    current_user: auth_models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(auth_models.ResearchHistory)
        .filter(
            auth_models.ResearchHistory.id == history_id,
            auth_models.ResearchHistory.user_id == current_user.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="History item not found")
    db.delete(item)
    db.commit()
    return None


@router.post(
    "/history",
    response_model=auth_schemas.HistoryListItemOut,
    status_code=status.HTTP_201_CREATED,
)
def save_history(
    payload: auth_schemas.SaveHistoryRequest,
    current_user: auth_models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Called by the frontend once a research run finishes, with the
    query + final report + full pipeline state. Keeps the DB session
    out of the /research streaming generator entirely.
    """
    item = auth_models.ResearchHistory(
        user_id=current_user.id,
        query=payload.query,
        final_report=payload.final_report,
        state_json=payload.state_json,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
