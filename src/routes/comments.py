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
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
    new_comment = await comments.create_comment(body, photos_id, current_user, db)
    return new_comment


@router.get("/{photo_id}/", response_model=list[CommentModel])
async def get_comments(photo_id: int, db: Session = Depends(get_db)):
    result = await comments.get_comments_by_photo_id(photo_id, db)
    return result


@router.get("/{comment_id}/", response_model=CommentModel)
async def get_comment(comment_id: int, db: Session = Depends(get_db)):
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
@router.delete("/{comment_id}/", response_model=CommentModel, dependencies = [Depends(allowed_roles_to_delete_comments)])
async def remove_comment(
        comment_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(auth_service.get_current_user),
        token: str = Depends(auth_service.oauth2_scheme),
):
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    comment = await comments.get_comment_by_id(comment_id, db)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    deleted_comment = await comments.delete_comment(comment_id, db)
    return deleted_comment
