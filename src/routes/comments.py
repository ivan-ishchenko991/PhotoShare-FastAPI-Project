from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from src.database.connect import get_db
from src.database.models import User
from src.repository import comments
from src.schemas import CommentBase, CommentModel
from src.services.auth import auth_service
from src.services.roles import RoleChecker

router = APIRouter(prefix='/comments', tags=["comments"])


@router.post("/{photos_id}", response_model=CommentModel)
async def create_comment(
        photos_id: int,
        body: CommentBase,
        db: Session = Depends(get_db),
        current_user: User = Depends(auth_service.get_current_user),
        token: str = Depends(auth_service.oauth2_scheme),
):
    """
    The create_comment function creates a new comment for the photo with the given id. The function takes in an
    integer representing the photos_id, and a CommentBase object containing the body of the comment. The function
    also takes in three optional parameters: db, current_user, and token. db is used to access our database using
    SQLAlchemy's ORM (Object Relational Mapper). current_user is used to get information about who created this
    comment (i.e., their username), while token is used to check if it has been blacklisted.

    :param photos_id: int: Specify the photo that the comment is being added to
    :param body: CommentBase: Get the body of the comment from the request
    :param db: Session: Pass the database session to the function
    :param current_user: User: Get the user who is making the request
    :param token: str: Check if the token is blacklisted
    :param : Get the id of the photo that is being commented on
    :return: A commentbase object
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
    new_comment = await comments.create_comment(body, photos_id, current_user, db)
    return new_comment


@router.get("/{photo_id}/", response_model=list[CommentModel])
async def get_comments(photo_id: int, db: Session = Depends(get_db)):
    """
    The get_comments function returns a list of comments for the photo with the given ID.

    :param photo_id: int: Get the comments for a specific photo
    :param db: Session: Get the database session
    :return: A list of comments that are associated with the photo
    """
    result = await comments.get_comments_by_photo_id(photo_id, db)
    return result


@router.get("/{comment_id}/", response_model=CommentModel)
async def get_comment(comment_id: int, db: Session = Depends(get_db)):
    """
    The get_comment function takes a comment_id and returns the Comment object with that id.
    If no such comment exists, it raises an HTTPException with status code 404.

    :param comment_id: int: Specify the id of the comment that is being requested
    :param db: Session: Pass the database session to the function
    :return: A comment object
    """
    comment = await comments.get_comment_by_id(comment_id, db)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return comment


@router.put("/{comment_id}", response_model=CommentModel)
async def update_comment(
        comment_id: int,
        comment: CommentBase,
        user: User = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db),
        token: str = Depends(auth_service.oauth2_scheme),
):
    """
    The update_comment function updates a comment in the database. It takes an id, a CommentBase object,
    and optionally a user and db session. If the user is not provided it will be retrieved from auth_service using
    the token provided by Depends(auth_service.oauth2_scheme). If no token is provided or if it's blacklisted then an
    HTTPException will be raised with status code 401 (UNAUTHORIZED) and detail &quot;Token is blacklisted&quot;. The
    function first checks to see if there's already a comment with that id in the database by calling comments.get

    :param comment_id: int: Identify the comment to be deleted
    :param comment: CommentBase: Pass the comment object to the update_comment function
    :param user: User: Get the current user
    :param db: Session: Pass the database session to the function
    :param token: str: Check if the token is blacklisted
    :param : Get the comment id of the comment to be deleted
    :return: The updated comment
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
    db_comment = await comments.get_comment_by_id(comment_id, db)
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if db_comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")
    comment_data = comment.dict()
    comment_data["updated_at"] = datetime.now()
    updated_comment = await comments.update_comment(comment_id, comment, db)
    return updated_comment

allowed_roles_to_delete_comments = RoleChecker(["Administrator", "Moderator"])


@router.delete("/{comment_id}/", response_model=CommentModel, dependencies=[Depends(allowed_roles_to_delete_comments)])
async def remove_comment(
        comment_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(auth_service.get_current_user),
        token: str = Depends(auth_service.oauth2_scheme),
):
    """
    The remove_comment function is used to delete a comment from the database. It takes in an integer representing
    the id of the comment to be deleted, and returns a Comment object with all of its fields set to None.


    :param comment_id: int: Specify the id of the comment to be deleted
    :param db: Session: Get a database session
    :param current_user: User: Get the current user from the database
    :param token: str: Check if the token is blacklisted
    :param : Get the comment id from the url
    :return: The deleted comment
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    comment = await comments.get_comment_by_id(comment_id, db)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    deleted_comment = await comments.delete_comment(comment_id, db)
    return deleted_comment
