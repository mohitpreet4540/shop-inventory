from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.dependencies import hash_password, verify_password, create_access_token, require_roles, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# =================================================================
# 1. ONE-TIME OWNER BOOTSTRAP
# =================================================================
# Open (no auth required) ONLY because no OWNER can exist yet to authorize it.
# It self-locks the moment an OWNER account exists. Run this immediately after
# your first deploy, before exposing the API publicly.
@router.post("/bootstrap-owner", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def bootstrap_owner(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_owner = db.query(models.User).filter(models.User.role == "OWNER").first()
    if existing_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An OWNER account already exists. Use POST /api/auth/users (as OWNER) to create additional accounts."
        )

    existing_username = db.query(models.User).filter(models.User.username == payload.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail=f"Username '{payload.username}' is already taken.")

    new_user = models.User(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        role="OWNER",
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# =================================================================
# 2. LOGIN (Issues JWT)
# =================================================================
@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account has been deactivated.")

    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return schemas.Token(access_token=access_token, username=user.username, role=user.role)


# =================================================================
# 3. CREATE ADMIN / CASHIER ACCOUNTS (OWNER only)
# =================================================================
@router.post("/users", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("OWNER")),
):
    if payload.role not in ("ADMIN", "CASHIER"):
        raise HTTPException(status_code=400, detail="role must be 'ADMIN' or 'CASHIER' (OWNER accounts are created only via bootstrap).")

    existing = db.query(models.User).filter(models.User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Username '{payload.username}' is already taken.")

    new_user = models.User(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# =================================================================
# 4. LIST USERS (OWNER, ADMIN)
# =================================================================
@router.get("/users", response_model=List[schemas.UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("OWNER", "ADMIN")),
):
    return db.query(models.User).all()


# =================================================================
# 5. DEACTIVATE / REACTIVATE A USER (OWNER only)
# =================================================================
@router.patch("/users/{user_id}/toggle-active", response_model=schemas.UserResponse)
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_roles("OWNER")),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.role == "OWNER":
        raise HTTPException(status_code=400, detail="Cannot deactivate an OWNER account.")

    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user


# =================================================================
# 6. CURRENT USER PROFILE
# =================================================================
@router.get("/me", response_model=schemas.UserResponse)
def get_my_profile(current_user: models.User = Depends(get_current_user)):
    return current_user
