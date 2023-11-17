from typing import List

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session

from src.conf import messages as message
from src.database.connect import get_db
from src.schemas import TagBase, TagResponse, Role
from src.repository import tags as repository_tags
from src.database.models import User
from src.services.roles import RoleChecker
from src.services.auth import auth_service

router = APIRouter(prefix='/tags', tags=["tags"])

allowed_get_all_tags = RoleChecker([Role.Administrator])
allowed_remove_tag = RoleChecker([Role.Administrator])
allowed_edit_tag = RoleChecker([Role.Administrator])


@router.post("/", response_model=TagResponse)
async def create_tag(body: TagBase,
                     db: Session = Depends(get_db),
                     current_user: User = Depends(auth_service.get_current_user),
                     token: str = Depends(auth_service.oauth2_scheme),
                     ):
    """
    The create_tag function creates a new tag in the database.
        It takes a TagBase object as input, which is validated by pydantic.
        The function returns the newly created tag.

    :param body: TagBase: Pass the tag data to the function
    :param db: Session: Get the database session
    :param current_user: User: Get the current user from the database
    :param token: str: Check if the token is blacklisted
    :param : Get the tag id
    :return: A tag object
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
    tag = await repository_tags.create_tag(body, db, current_user)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=message.TAG_ALREADY_EXISTS
        )
    return tag


@router.get("/my/", response_model=List[TagResponse])
async def read_my_tags(skip: int = 0,
                       limit: int = 100,
                       db: Session = Depends(get_db),
                       current_user: User = Depends(auth_service.get_current_user),
                       token: str = Depends(auth_service.oauth2_scheme),
                       ):
    """
    The read_my_tags function returns a list of tags that the current user has created.

    :param skip: int: Skip the first n tags
    :param limit: int: Limit the number of tags returned
    :param db: Session: Get the database session
    :param current_user: User: Get the current user from the database
    :param token: str: Verify that the token is not blacklisted
    :param : Get the current user
    :return: A list of tags
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
    tags = await repository_tags.get_my_tags(skip, limit, db, current_user)
    return tags


@router.get("/all/", response_model=List[TagResponse], dependencies=[Depends(allowed_get_all_tags)])
async def read_all_tags(skip: int = 0,
                        limit: int = 100,
                        db: Session = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user),
                        token: str = Depends(auth_service.oauth2_scheme),
                        ):
    """
    The read_all_tags function returns a list of all tags in the database.

    :param skip: int: Skip the first n tags
    :param limit: int: Limit the number of tags returned
    :param db: Session: Get the database session
    :param current_user: User: Get the user that is currently logged in
    :param token: str: Check if the token is blacklisted
    :param : Get the tag id from the url
    :return: A list of tags
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
    tags = await repository_tags.get_all_tags(skip, limit, db)
    return tags


@router.get("/{tag_id}", response_model=TagResponse)
async def read_tag_by_id(tag_id: int,
                         db: Session = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user),
                         token: str = Depends(auth_service.oauth2_scheme),
                         ):
    """
    The read_tag_by_id function is used to read a tag by its id.

    :param tag_id: int: Get the tag by id
    :param db: Session: Pass the database session to the function
    :param current_user: User: Get the current user from the database
    :param token: str: Check if the token is blacklisted
    :param : Get the tag id from the url
    :return: A tag object
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
    tag = await repository_tags.get_tag_by_id(tag_id, db)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message.NOT_FOUND)
    return tag


@router.put("/{tag_id}", response_model=TagResponse, dependencies=[Depends(allowed_edit_tag)])
async def update_tag(body: TagBase,
                     tag_id: int,
                     db: Session = Depends(get_db),
                     current_user: User = Depends(auth_service.get_current_user),
                     token: str = Depends(auth_service.oauth2_scheme),
                     ):
    """
    The update_tag function updates a tag in the database.
        The function takes three arguments:
            - body: A TagBase object containing the new values for the tag.
            - tag_id: An integer representing the id of an existing tag to be updated.
            - db (optional): A Session object used to connect to and query from a database, defaults to None.

    :param body: TagBase: Get the new tag name
    :param tag_id: int: Identify the tag to be deleted
    :param db: Session: Get the database session
    :param current_user: User: Get the current user
    :param token: str: Check if the token is blacklisted
    :param : Get the tag id
    :return: A tag object
    :doc-author: Trelent
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
    tag = await repository_tags.update_tag(tag_id, body, db)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message.NOT_FOUND)
    return tag


@router.delete("/{tag_id}", response_model=TagResponse, dependencies=[Depends(allowed_remove_tag)])
async def remove_tag(tag_id: int,
                     db: Session = Depends(get_db),
                     current_user: User = Depends(auth_service.get_current_user),
                     token: str = Depends(auth_service.oauth2_scheme),
                     ):
    """
    The remove_tag function removes a tag from the database.
        It takes in an integer representing the id of the tag to be removed, and returns a Tag object.

    :param tag_id: int: Identify the tag to be removed
    :param db: Session: Get the database session
    :param current_user: User: Get the user that is currently logged in
    :param token: str: Get the token from the request header
    :param : Get the tag id from the request
    :return: The tag that was removed
    :doc-author: Trelent
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
    tag = await repository_tags.remove_tag(tag_id, db)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message.NOT_FOUND)
    return tag
