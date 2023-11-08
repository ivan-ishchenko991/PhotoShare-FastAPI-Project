from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Dict
from src.database.connect import get_db
from src.database.models import User, Photo
from src.repository.photos import get_user_photos
from src.schemas import UserDb, UserUpdate, AdminUserPatch
from src.repository import users as repository_users
from src.services.auth import auth_service

router = APIRouter(prefix='/users', tags=["users"])


# Рахуємо фото
def get_user_photos_count(user_id: int, db: Session) -> int:
    photos_count = db.query(Photo).filter(Photo.user_id == user_id).count()
    return photos_count


# Профіль користувача

@router.get("/me/", response_model=UserDb)
async def read_users_me(
        current_user: UserDb = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db),
        ):
    photos_count = get_user_photos_count(current_user.id, db)

    current_user.photos_count = photos_count

    return current_user


# Редагування профілю користувача

@router.put("/edit", response_model=Dict[str, str])
async def edit_user_profile(
        user_update: UserUpdate,
        current_user: UserDb = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db),
        ):
    user = await repository_users.get_user_by_id(current_user.id, db)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.email is not None:
        existing_user = await repository_users.get_user_by_email(user_update.email, db)
        if existing_user and existing_user.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This user already exists. Please enter another email",
            )
        user.email = user_update.email

    if user_update.username is not None:
        user.username = user_update.username

    if user_update.password is not None:
        password = user_update.password.get_secret_value()
        user.password = auth_service.get_password_hash(password)

    db.commit()
    db.refresh(user)

    return {"message": "Data changed successfully"}


# Редагування профілю користувача

@router.patch("/patch/{user_id}", response_model=Dict[str, str])
async def patch_user_profile(
        user_id: int,
        user_update: AdminUserPatch,
        current_user: UserDb = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db),
        ):
    if not current_user or "Administrator" not in current_user.roles.split(","):
        raise HTTPException(status_code=403, detail="Permission denied")

    user = await repository_users.get_user_by_id(user_id, db)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user_update.email is not None:
        existing_user = await repository_users.get_user_by_email(user_update.email, db)
        if existing_user and existing_user.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This user already exists. Please enter another email",
            )
        user.email = user_update.email

    if user_update.username is not None:
        user.username = user_update.username

    if user_update.password is not None:
        password = user_update.password.get_secret_value()
        user.password = auth_service.get_password_hash(password)

    if user_update.is_active is not None:
        user.is_active = user_update.is_active

    db.commit()
    db.refresh(user)

    return {"message": "Data changed successfully"}