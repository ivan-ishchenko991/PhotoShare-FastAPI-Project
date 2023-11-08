from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer

from src.schemas import (
    PhotoCreate,
    PhotoUpdate,
    PhotoResponse,
    PhotoListResponse,
    TagResponse
)
from src.services.auth import auth_service
from src.database.connect import get_db
from src.database.models import Photo, User
from src.repository import photos as repository_photos

router = APIRouter(prefix='/photos', tags=["photos"])
security = HTTPBearer()


@router.post("/", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
async def create_user_photo(
        image: UploadFile = File(...),
        description: str = Form(...),
        tags: List[str] = Form([]),
        db: Session = Depends(get_db),
        current_user: User = Depends(auth_service.get_current_user),
        ):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if len(tags) > 5:
        raise HTTPException(status_code=400, detail="Too many tags provided")

    photo_data = PhotoCreate(description=description, tags=tags)
    return repository_photos.create_user_photo(photo_data, image, current_user, db)


@router.get("/", response_model=PhotoListResponse)
async def get_user_photos(
        skip: int = 0,
        limit: int = 10,
        db: Session = Depends(get_db),
        current_user: User = Depends(auth_service.get_current_user),
):
    if "Administrator" in current_user.roles:
        user_id = None  # Адміністратор має доступ до фотографій будь-якого користувача
    else:
        user_id = current_user.id

    photos = repository_photos.get_user_photos(user_id, skip, limit, db)
    return {"photos": photos}


@router.get("/{photo_id}", response_model=PhotoResponse)
async def get_user_photo_by_id(
        photo_id: int,
        current_user: User = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db),
):
    if "Administrator" in current_user.roles.split(","):
        user_id = None  # Адміністратор має доступ до фотографій будь-якого користувача
    else:
        user_id = current_user.id

    photo = (
        db.query(Photo)
        .filter(Photo.id == photo_id, (Photo.user_id == user_id) | (user_id == None))
        .first()
    )

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found"
        )

    return PhotoResponse(
        id=photo.id,
        image_url=photo.image_url,
        description=photo.description,
        created_at=photo.created_at,
        updated_at=photo.updated_at,
        tags=[TagResponse(id=tag.id, title=tag.title, created_at=tag.created_at) for tag in photo.tags]
    )


@router.put("/{photo_id}", response_model=PhotoResponse)
async def update_user_photo(
        photo_id: int,
        updated_photo: PhotoUpdate,
        current_user: User = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db),
):
    photo = repository_photos.get_user_photo_by_id(photo_id, db)

    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found"
        )

    if not (
            current_user
            and ("Administrator" in current_user.roles.split(","))
            or current_user.id == photo.user_id
    ):
        raise HTTPException(status_code=403, detail="Permission denied")

    updated_photo = repository_photos.update_user_photo(photo, updated_photo, current_user, db)
    return updated_photo


@router.delete("/{photo_id}", response_model=PhotoResponse)
async def delete_user_photo(
        photo_id: int,
        current_user: User = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db),
):
    if not current_user:
        raise HTTPException(
            status_code=403, detail="Permission denied"
        )  # Користувач повинен бути авторизований для видалення фото

    is_admin = "Administrator" in current_user.roles.split(",")

    result = await repository_photos.delete_user_photo(
        photo_id, current_user.id, is_admin, db
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found"
        )

    response_data = {
        "id": result.id,
        "image_url": result.image_url,
        "description": result.description,
        "created_at": result.created_at,
        "updated_at": result.updated_at,
        "tags": result.tags
    }

    return response_data
