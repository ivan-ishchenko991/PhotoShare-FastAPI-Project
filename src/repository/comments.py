from sqlalchemy.orm import Session
from src.database.models import Comment, User
from src.schemas import CommentBase


async def create_comment(comment: CommentBase, photo_id: int, current_user: User, db: Session):
    db_comment = Comment(**comment.dict(), user_id=current_user.id, photo_id=photo_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


async def get_comments_by_photo_id(photo_id: int, db: Session):
    return db.query(Comment).filter(Comment.photo_id == photo_id).all()


async def get_comment_by_id(comment_id: int, db: Session):
    return db.query(Comment).filter(Comment.id == comment_id).first()


async def update_comment(comment_id: int, comment: CommentBase, db: Session):
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if db_comment:
        for key, value in comment.dict().items():
            setattr(db_comment, key, value)
        db.commit()
        db.refresh(db_comment)
        return db_comment
    return None


async def delete_comment(comment_id: int, db: Session):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if comment:
        db.delete(comment)
        db.commit()
        return comment
    return None
