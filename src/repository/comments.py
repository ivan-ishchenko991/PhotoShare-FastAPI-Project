from sqlalchemy.orm import Session
from models import Comment

def create_comment(db: Session, comment: CommentIn, user_id: int, photo_id: int):
    db_comment = Comment(**comment.dict(), user_id=user_id, photo_id=photo_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def get_comments_by_photo_id(db: Session, photo_id: int):
    return db.query(Comment).filter(Comment.photo_id == photo_id).all()

def get_comment_by_id(db: Session, comment_id: int):
    return db.query(Comment).filter(Comment.id == comment_id).first()

def update_comment(db: Session, comment_id: int, comment: CommentIn):
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if db_comment:
        for key, value in comment.dict().items():
            setattr(db_comment, key, value)
        db.commit()
        db.refresh(db_comment)
        return db_comment
    return None

def delete_comment(db: Session, comment_id: int):
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if comment:
        db.delete(comment)
        db.commit()
        return comment
    return None
