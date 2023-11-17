from sqlalchemy.orm import Session
from src.database.models import Comment, User
from src.schemas import CommentBase


async def create_comment(comment: CommentBase, photo_id: int, current_user: User, db: Session):
    """
    The create_comment function creates a new comment in the database.
        Args:
            comment (CommentBase): The CommentBase object to be created.
            photo_id (int): The id of the photo that this comment is associated with.
            current_user (User): The user who is creating this comment. This will be used to set the author of the new Comment object, and also for authorization purposes later on in our codebase when we want to make sure that only authorized users can delete comments they have created themselves.

    :param comment: CommentBase: Pass in the comment object that is created by the user
    :param photo_id: int: Identify the photo that the comment is being made on
    :param current_user: User: Get the user_id of the current user
    :param db: Session: Access the database
    :return: The created comment
    """
    db_comment = Comment(**comment.dict(), user_id=current_user.id, photo_id=photo_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


async def get_comments_by_photo_id(photo_id: int, db: Session):
    """
    The get_comments_by_photo_id function returns all comments associated with a given photo_id.
        Args:
            photo_id (int): The id of the photo to be queried for comments.
            db (Session): A database session object used to query the database.

    :param photo_id: int: Filter the comments by photo_id
    :param db: Session: Pass the database session to the function
    :return: All comments for a given photo id
    """
    return db.query(Comment).filter(Comment.photo_id == photo_id).all()


async def get_comment_by_id(comment_id: int, db: Session):
    """
    The get_comment_by_id function takes in a comment_id and db Session object,
    and returns the Comment object with that id. If no such Comment exists, it returns None.

    :param comment_id: int: Specify the id of the comment to be retrieved
    :param db: Session: Pass in the database session object
    :return: A comment object
    """
    return db.query(Comment).filter(Comment.id == comment_id).first()


async def update_comment(comment_id: int, comment: CommentBase, db: Session):
    """
    The update_comment function updates a comment in the database.
        Args:
            comment_id (int): The id of the comment to update.
            comment (CommentBase): The updated version of the Comment object.

    :param comment_id: int: Identify the comment to be deleted
    :param comment: CommentBase: Pass in the new comment data
    :param db: Session: Access the database
    :return: A comment object
    """
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if db_comment:
        for key, value in comment.dict().items():
            setattr(db_comment, key, value)
        db.commit()
        db.refresh(db_comment)
        return db_comment
    return None


async def delete_comment(comment_id: int, db: Session):
    """
    The delete_comment function deletes a comment from the database.
        Args:
            comment_id (int): The id of the comment to be deleted.
            db (Session): A connection to the database.

    :param comment_id: int: Identify the comment to be deleted
    :param db: Session: Pass the database session to the function
    :return: The deleted comment object
    """
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if comment:
        db.delete(comment)
        db.commit()
        return comment
    return None
