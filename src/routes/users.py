from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Dict
from sqlalchemy.orm import Session
from src.database.connect import get_db
from src.database.models import User, Photo, Roles
from src.repository.photos import get_user_photos
from src.schemas import UserDb, UserUpdate, AdminUserPatch
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.services.roles import RoleChecker

router = APIRouter(prefix='/users', tags=["users"])

allowed_roles_to_block = RoleChecker(["Administrator"])
allowed_roles_to_change_role = RoleChecker(["Administrator"])
allowed_roles_to_delete_like = RoleChecker(["Administrator", "Moderator"])


# загальна кількість фотографій у базі

def get_user_photos_count(user_id: int, db: Session) -> int:
    """
        Retrieves the count of photos associated with a user.

        Parameters:
        - `user_id` (int): The identifier of the user for whom to retrieve the photo count.
        - `db` (Session): The database session object.

        Returns:
        - `int`: The count of photos associated with the specified user.
        """
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


@router.patch("/like")
async def put_like(photo_id: int,
                   current_user: User = Depends(auth_service.get_current_user),
                   db: Session = Depends(get_db),
                   ):
    """Parameters:
    - `photo_id` (int): The identifier of the photo that the user wants to like.
    - `current_user` (User): The user object representing the requester (obtained as a dependency from the `get_current_user` function).
    - `db` (Session): The database session object (obtained as a dependency from the `get_db` function).

    Returns:
    - `dict`: A JSON object with a message indicating successful liking of the photo, or raises an HTTPException with status code 403
      if the user has already liked the photo.
    """
    result = await repository_users.put_a_like(photo_id, current_user, db)
    if result == "NOT OK":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You have already liked this photo")
    return {"message": "You have successfully liked a photo"}


@router.patch("/remove_like")
async def remove_like(photo_id: int,
                      current_user: User = Depends(auth_service.get_current_user),
                      db: Session = Depends(get_db),
                      ):
    """
    Parameters:
    - `photo_id` (int): The identifier of the photo from which the user wants to remove the like.
    - `current_user` (User): The user object representing the requester (obtained as a dependency from the `get_current_user` function).
    - `db` (Session): The database session object (obtained as a dependency from the `get_db` function).

    Returns:
    - `dict`: A JSON object with a message indicating successful removal of the like from the photo, or raises an HTTPException with status code 403
      if the user has not liked the photo before.
    """
    result = await repository_users.dislike(photo_id, current_user, db)
    if result == "NOT OK":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You have already unliked this photo")
    return {"message": "You have removed a like from a photo"}


@router.patch("/admin_moder_dislike", dependencies=[Depends(allowed_roles_to_delete_like)])
async def delete_someones_like(user_email: str,
                               photo_id: int,
                               current_user: User = Depends(auth_service.get_current_user),
                               db: Session = Depends(get_db)
                               ):
    """Parameters:
    - `user_email` (str): The email of the user whose like is to be removed.
    - `photo_id` (int): The identifier of the photo from which the user's like is to be removed.
    - `current_user` (User): The user object representing the requester (obtained as a dependency from the `get_current_user` function).
    - `db` (Session): The database session object (obtained as a dependency from the `get_db` function).

    Returns:
    - `dict`: A JSON object with a message indicating successful removal of the user's like from the photo, or raises an HTTPException with status code 404
      if the user did not like the photo before.
    """
    result = await repository_users.delete_like_admin_moder(user_email, photo_id, db)
    if result == "NOT OK":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"The user {user_email} did not like this photo!")
    return {"message": f"The user's ({user_email}) like has been removed from the photo {photo_id}!"}


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


@router.patch("/change_role", dependencies=[Depends(allowed_roles_to_change_role)])
async def change_role(user_email: str,
                      role: Roles = Query(..., description="User role"),
                      current_user: User = Depends(auth_service.get_current_user),
                      db: Session = Depends(get_db)
                      ):
    """
       Processes a request to change the role of a user.

       Parameters:
       - `user_email` (str): The email of the user whose role is to be changed.
       - `role` (Roles): The new role to assign to the user.
       - `current_user` (User): The user object representing the requester (obtained as a dependency from the `get_current_user` function).
       - `db` (Session): The database session object (obtained as a dependency from the `get_db` function).

       Returns:
       - `dict`: A JSON object with a message indicating successful role change, or raises an HTTPException with status code 403
         if changing the role for an admin is forbidden.
    """
    print(role)
    result = await repository_users.change_role(user_email, role, db)
    if result == "NOT OK":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Changing role for admin is forbidden")
    return {"message": "User role changed"}


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

        Raises: HTTPException: If the provided token is blacklisted, user is not found, or if there are conflicts
        during the update.
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
    user = await repository_users.get_user_by_email(current_user.email, db)

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
        email: str,
        user_update: AdminUserPatch,
        current_user: UserDb = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db),
        token: str = Depends(auth_service.oauth2_scheme),
):
    """
        Partially update the profile of a user by their email, with admin privileges.

        Parameters: - email (str) - user_update (AdminUserPatch): Partial user data
        to be updated, including email, username, password, and is_active status. - current_user (UserDb): The
        authenticated user obtained from the token with admin privileges. - db (Session): SQLAlchemy database session
        for updating user profile in the database. - token (str): OAuth2 token for user authentication.

        Returns:
        Dict[str, str]: A message indicating successful data change.

        Raises: HTTPException: If the provided token is blacklisted, user is not an administrator, user is not found,
        or if there are conflicts during the update.
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
    if not current_user or "Administrator" not in current_user.roles.split(","):
        raise HTTPException(status_code=403, detail="Permission denied")

    user = await repository_users.get_user_by_email(email, db)

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
