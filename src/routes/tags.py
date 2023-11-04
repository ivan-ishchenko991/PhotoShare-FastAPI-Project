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

router = APIRouter(tags=["tags"])

allowed_get_all_tags = RoleChecker([Role.Administrator])
allowed_remove_tag = RoleChecker([Role.Administrator])
allowed_edit_tag = RoleChecker([Role.Administrator])


@router.post("/", response_model=TagResponse)
async def create_tag(body: TagBase,
                     db: Session = Depends(get_db),
                     current_user: User = Depends(auth_service.get_current_user)
                     ):
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
                       current_user: User = Depends(auth_service.get_current_user)
                       ):
    tags = await repository_tags.get_my_tags(skip, limit, db, current_user)
    return tags


@router.get("/all/", response_model=List[TagResponse], dependencies=[Depends(allowed_get_all_tags)])
async def read_all_tags(skip: int = 0,
                        limit: int = 100,
                        db: Session = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user)
                        ):
    tags = await repository_tags.get_all_tags(skip, limit, db)
    return tags


@router.get("/{tag_id}", response_model=TagResponse)
async def read_tag_by_id(tag_id: int,
                         db: Session = Depends(get_db),
                         current_user: User = Depends(auth_service.get_current_user)
                         ):
    tag = await repository_tags.get_tag_by_id(tag_id, db)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message.NOT_FOUND)
    return tag


@router.put("/{tag_id}", response_model=TagResponse, dependencies=[Depends(allowed_edit_tag)])
async def update_tag(body: TagBase,
                     tag_id: int,
                     db: Session = Depends(get_db),
                     current_user: User = Depends(auth_service.get_current_user)
                     ):
    tag = await repository_tags.update_tag(tag_id, body, db)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message.NOT_FOUND)
    return tag


@router.delete("/{tag_id}", response_model=TagResponse, dependencies=[Depends(allowed_remove_tag)])
async def remove_tag(tag_id: int,
                     db: Session = Depends(get_db),
                     current_user: User = Depends(auth_service.get_current_user)
                     ):
    tag = await repository_tags.remove_tag(tag_id, db)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message.NOT_FOUND)
    return tag
