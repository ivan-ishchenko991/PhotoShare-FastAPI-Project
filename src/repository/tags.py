from typing import List

from sqlalchemy.orm import Session

from src.database.models import Tag, User
from src.schemas import TagBase


async def create_tag(body: TagBase,
                     db: Session,
                     user: User
                     ) -> Tag | None:
    """
    The create_tag function creates a new tag in the database.

    :param body: TagBase: Define the body of the request
    :param db: Session: Access the database
    :param user: User: Get the user_id from the logged in user
    :return: A tag object, but it is not used in the code
    """
    tag = db.query(Tag).filter(Tag.title == body.title).first()
    if not tag:
        tag = Tag(
            title=body.title,
            user_id=user.id
        )
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag
    else:
        return None


async def get_my_tags(skip: int,
                      limit: int,
                      db: Session,
                      user: User) -> List[Tag]:
    """
    The get_my_tags function returns a list of tags that belong to the user.

    :param skip: int: Skip a number of tags in the database
    :param limit: int: Limit the number of tags returned
    :param db: Session: Pass in a database session
    :param user: User: Get the user's id and then filter the tags by that id
    :return: A list of tags
    """
    return db.query(Tag).filter(Tag.user_id == user.id).offset(skip).limit(limit).all()


async def get_all_tags(skip: int,
                       limit: int,
                       db: Session
                       ) -> List[Tag]:
    """
    The get_all_tags function returns a list of all tags in the database.

    :param skip: int: Skip a certain number of tags
    :param limit: int: Limit the number of tags returned
    :param db: Session: Pass the database session to the function
    :return: A list of all the tags in the database
    """
    return db.query(Tag).offset(skip).limit(limit).all()


async def get_tag_by_id(tag_id: int,
                        db: Session
                        ) -> Tag:
    """
    The get_tag_by_id function returns a Tag object from the database, given its id.

    :param tag_id: int: Filter the database query to return only the tag with a matching id
    :param db: Session: Pass the database session to the function
    :return: A tag object based on the id of a tag
    """
    return db.query(Tag).filter(Tag.id == tag_id).first()


async def update_tag(tag_id: int,
                     body: TagBase,
                     db: Session
                     ) -> Tag | None:
    """
    The update_tag function updates a tag in the database.
        Args:
            tag_id (int): The id of the tag to update.
            body (TagBase): The updated information for the specified Tag.

    :param tag_id: int: Identify the tag to be deleted
    :param body: TagBase: Pass the new title of the tag to be updated
    :param db: Session: Pass the database session to the function
    :return: The updated tag
    """
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if tag:
        tag.title = body.title
        db.commit()
    return tag


async def remove_tag(tag_id: int,
                     db: Session
                     ) -> Tag | None:
    """
    The remove_tag function removes a tag from the database.
        Args:
            tag_id (int): The id of the tag to be removed.
            db (Session): A connection to the database.

    :param tag_id: int: Specify the id of the tag to be deleted
    :param db: Session: Pass the database session to the function
    :return: The tag that was removed
    """
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if tag:
        db.delete(tag)
        db.commit()
    return tag
