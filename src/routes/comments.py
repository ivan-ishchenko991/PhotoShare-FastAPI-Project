from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from repository import create_comment, get_comments_by_photo_id, get_comment_by_id, update_comment, delete_comment
from models import Comment
from auth import get_current_user

router = APIRouter()

@router.post("/comments/", response_model=schemas.Comment)
def create_comment(comment: schemas.CommentIn, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return crud.create_comment(db, comment, user.id)

@router.get("/comments/{photo_id}/", response_model=list[Comment])
def get_comments(photo_id: int, db: Session = Depends(get_db)):
    comments = get_comments_by_photo_id(db, photo_id)
    return comments

@router.get("/comments/{comment_id}/", response_model=Comment)
def get_comment(comment_id: int, db: Session = Depends(get_db)):
    comment = get_comment_by_id(db, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return comment

@router.put("/comments/{comment_id}", response_model=schemas.Comment)
def update_comment(comment_id: int, comment: schemas.CommentIn, user: schemas.User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_comment = crud.get_comment(db, comment_id)
    if db_comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    if db_comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")
    return crud.update_comment(db, comment_id, comment)

@router.delete("/comments/{comment_id}/", response_model=Comment)
def remove_comment(comment_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
    
    comment = get_comment_by_id(db, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    
    if is_admin(current_user) or is_moderator(current_user):
        deleted_comment = delete_comment(db, comment_id)
        return deleted_comment
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to delete comment")
