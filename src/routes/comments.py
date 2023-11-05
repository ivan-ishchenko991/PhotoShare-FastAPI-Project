from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from src.database.connect import get_db
from src.repository.comments import create_comment, get_comments_by_photo_id, get_comment_by_id, update_comment, delete_comment
from src.schemas import CommentBase, CommentModel
from src.services.auth import auth_service

router = APIRouter(tags=["comments"])

@router.post("/{photos_id}", response_model=CommentModel)
def create_comment(
    photos_id: int,
    body: CommentBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    new_comment = create_comment(photos_id, body, db, current_user)
    return new_comment

@router.get("/{photo_id}/", response_model=list[CommentModel])
def get_comments(photo_id: int, db: Session = Depends(get_db)):
    comments = get_comments_by_photo_id(db, photo_id)
    return comments

@router.get("/{comment_id}/", response_model=CommentModel)
def get_comment(comment_id: int, db: Session = Depends(get_db)):
    comment = get_comment_by_id(db, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    return comment

@router.put("/{comment_id}", response_model=CommentModel)
def update_comment(
    comment_id: int,
    comment: CommentBase,
    user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    db_comment = get_comment_by_id(db, comment_id)
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if db_comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")
    comment_data = comment.dict()
    comment_data["updated_at"] = datetime.now()
    updated_comment = update_comment(db, comment_id, comment_data)
    return updated_comment

@router.delete("/{comment_id}/", response_model=CommentModel)
def remove_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    comment = get_comment_by_id(db, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    if (
        auth_service.is_admin(current_user) or
        auth_service.is_moderator(current_user)
    ):
        deleted_comment = delete_comment(db, comment_id)
        return deleted_comment
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to delete comment")
