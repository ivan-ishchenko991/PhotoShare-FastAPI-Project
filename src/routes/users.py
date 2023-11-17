from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict
from sqlalchemy.orm import Session
from src.database.connect import get_db
from src.database.models import User, Photo
from src.repository.photos import get_user_photos
from src.schemas import UserDb, UserUpdate, AdminUserPatch
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.services.roles import RoleChecker

router = APIRouter(prefix='/users', tags=["users"])

allowed_roles_to_block = RoleChecker(["Administrator"])


# загальна кількість фотографій у базі

def get_user_photos_count(user_id: int, db: Session) -> int:
    photos_count = db.query(Photo).filter(Photo.user_id == user_id).count()
    return photos_count


# Створюємо загальний профіль користувачів

@router.get("/me/", response_model=UserDb)
async def read_users_me(
        current_user: UserDb = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db),
        token: str = Depends(auth_service.oauth2_scheme),
):
    """
        Get information about the currently authenticated user.

        Parameters:
        - current_user (UserDb): The authenticated user obtained from the token.
        - db (Session): SQLAlchemy database session for querying user data.
        - token (str): OAuth2 token for user authentication.

        Returns:
        UserDb: User database model containing information about the authenticated user.

        Raises:
        HTTPException: If the provided token is blacklisted, returns a 401 UNAUTHORIZED error.
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
    photos_count = get_user_photos_count(current_user.id, db)

    current_user.photos_count = photos_count

    return current_user


@router.post("/block", dependencies=[Depends(allowed_roles_to_block)])
async def blocking_user(user_email: str,
                        current_user: User = Depends(auth_service.get_current_user),
                        db: Session = Depends(get_db),
                        token: str = Depends(auth_service.oauth2_scheme),
                        ):
    """
        Block a user by email, restricting their access.

        Parameters:
        - user_email (str): Email of the user to be blocked.
        - current_user (User): The authenticated user obtained from the token.
        - db (Session): SQLAlchemy database session for blocking user in the database.
        - token (str): OAuth2 token for user authentication.

        Returns:
        dict: A message indicating successful user blocking.

        Raises:
        HTTPException: If there are issues blocking the user or if the current user lacks the required permissions.
    """
    await repository_users.block_user(user_email, db)
    return {"message": "User blocked"}


# Редагуємо профіль користувача

@router.put("/edit", response_model=Dict[str, str])
async def edit_user_profile(
        user_update: UserUpdate,
        current_user: UserDb = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db),
        token: str = Depends(auth_service.oauth2_scheme),
):
    """
        Edit the profile of the currently authenticated user.

        Parameters:
        - user_update (UserUpdate): User data to be updated, including email, username, and password.
        - current_user (UserDb): The authenticated user obtained from the token.
        - db (Session): SQLAlchemy database session for updating user profile in the database.
        - token (str): OAuth2 token for user authentication.

        Returns:
        Dict[str, str]: A message indicating successful data change.

        Raises:
        HTTPException: If the provided token is blacklisted, user is not found, or if there are conflicts during the update.
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
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


# Редагування профілю користувача putch

@router.patch("/patch/{user_id}", response_model=Dict[str, str])
async def patch_user_profile(
        user_id: int,
        user_update: AdminUserPatch,
        current_user: UserDb = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db),
        token: str = Depends(auth_service.oauth2_scheme),
):
    """
        Partially update the profile of a user by their ID, with admin privileges.

        Parameters:
        - user_id (int): ID of the user to be patched.
        - user_update (AdminUserPatch): Partial user data to be updated, including email, username, password, and is_active status.
        - current_user (UserDb): The authenticated user obtained from the token with admin privileges.
        - db (Session): SQLAlchemy database session for updating user profile in the database.
        - token (str): OAuth2 token for user authentication.

        Returns:
        Dict[str, str]: A message indicating successful data change.

        Raises:
        HTTPException: If the provided token is blacklisted, user is not an administrator, user is not found, or if there are conflicts during the update.
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
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
