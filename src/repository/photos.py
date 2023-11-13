from datetime import datetime
from typing import List

from fastapi import UploadFile
import cloudinary
from cloudinary.uploader import upload
from cloudinary.uploader import destroy
from sqlalchemy.orm import Session
from fastapi.exceptions import HTTPException

from src.database.models import Photo, User, Tag
from src.conf.config import settings
from src.schemas import PhotoCreate, PhotoUpdate, PhotoListResponse, TagResponse, PhotoResponse


def init_cloudinary():
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )


def get_public_id_from_image_url(image_url: str) -> str:
    parts = image_url.split("/")
    public_id = parts[-1]
    public_id = public_id.replace('%40', '@')
    return public_id


def create_user_photo(photo: PhotoCreate, image: UploadFile, current_user: User, db: Session) -> PhotoResponse:
    init_cloudinary()
    # Створюю унікальний public_id на основі поточного часу
    timestamp = datetime.now().timestamp()
    public_id = f"{current_user.email}_{current_user.id}_{int(timestamp)}"

    # image_bytes = image.file.read()
    cloudinary.uploader.upload(image.file, public_id=public_id, overwrite=True)
    image_url = cloudinary.CloudinaryImage(public_id).build_url(crop='fill')
    photo_data = photo.dict()
    photo_data["image_url"] = image_url
    photo_data["user_id"] = current_user.id
    photo_data["public_id"] = public_id

    tag_titles = [tag.strip() for tag in photo_data['tags'][0].split(",") if tag.strip()]
    if len(tag_titles) > 5:
        raise HTTPException(status_code=400, detail="Too many tags provided")
    tag_objects = []
    for tag_name in tag_titles:
        tag = db.query(Tag).filter(Tag.title == tag_name).first()
        if not tag:
            tag = Tag(title=tag_name, user_id=current_user.id)
            db.add(tag)
            db.commit()
            db.refresh(tag)
        tag_objects.append(tag)
    photo_data['tags'] = tag_objects
    db_photo = Photo(**photo_data)
    db_photo.tags = tag_objects

    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)

    photo_response_data = db_photo.__dict__
    photo_response_data["tags"] = [TagResponse(id=tag.id, title=tag.title, created_at=tag.created_at) for tag in
                                   db_photo.tags]
    photo_response_data.pop("_sa_instance_state", None)

    return PhotoResponse(**photo_response_data)


def get_user_photos(user_id: int, skip: int, limit: int, db: Session) -> list[PhotoResponse]:
    photos_query = db.query(Photo)
    # Якщо user_id має значення None, не фільтруємо за user_id
    if user_id is not None:
        photos_query = photos_query.filter(Photo.user_id == user_id)
    photos = photos_query.offset(skip).limit(limit).all()

    return [PhotoResponse(
        id=photo.id,
        image_url=photo.image_url,
        qr_transform=photo.qr_transform,
        description=photo.description,
        created_at=photo.created_at,
        updated_at=photo.updated_at,
        tags=[TagResponse(id=tag.id, title=tag.title, created_at=tag.created_at) for tag in photo.tags]
    ) for photo in photos]


def get_user_photo_by_id(photo_id: int, db: Session, current_user: User) -> PhotoResponse:
    if "Administrator" in current_user.roles.split(","):
        user_id = None  # Адміністратор має доступ до фотографій будь-якого користувача
    else:
        user_id = current_user.id

    photo = db.query(Photo).filter(Photo.id == photo_id, (Photo.user_id == user_id) | (user_id == None)).first()
    if not photo:
        return None

    return PhotoResponse(
        id=photo.id,
        image_url=photo.image_url,
        qr_transform=photo.qr_transform,
        description=photo.description,
        created_at=photo.created_at,
        updated_at=photo.updated_at,
        tags=[TagResponse(id=tag.id, title=tag.title, created_at=tag.created_at) for tag in photo.tags]
    )


def get_user_photo_by_id(photo_id: int, db: Session) -> Photo:
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    return photo


def update_user_photo(photo: Photo, updated_photo: PhotoUpdate, current_user: User, db: Session) -> PhotoResponse:
    if updated_photo.description is not None:
        photo.description = updated_photo.description

    if updated_photo.tags:
        tag_objects = []
        for tag_name in updated_photo.tags:
            tag = db.query(Tag).filter(Tag.title == tag_name, ).first()
            if not tag:
                tag = Tag(title=tag_name, user_id=current_user.id)
                db.add(tag)
            tag_objects.append(tag)
        photo.tags = tag_objects

    photo.updated_at = datetime.utcnow()  # Оновлення поля updated_at
    db.commit()
    return PhotoResponse(
        id=photo.id,
        image_url=photo.image_url,
        qr_transform=photo.qr_transform,
        description=photo.description,
        created_at=photo.created_at,
        updated_at=photo.updated_at,
        tags=[TagResponse(id=tag.id, title=tag.title, created_at=tag.created_at) for tag in photo.tags]
    )


async def delete_user_photo(photo_id: int, user_id: int, is_admin: bool, db: Session):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()

    if not photo:
        return None  # Фото не знайдено

    if not is_admin and user_id != photo.user_id:
        raise HTTPException(status_code=403, detail="Permission denied")  # Користувач може видаляти лише свої фото

    # Видалення фотографії з Cloudinary за її public_id
    public_id = get_public_id_from_image_url(photo.image_url)
    print(public_id)

    init_cloudinary()
    destroy(public_id, resource_type='image', type="upload")
    destroy("PhotoshareApp_qrcode/" + public_id + '_qr')
    destroy("PhotoshareApp_tr/" + public_id + '_qr')

    db.delete(photo)
    db.commit()

    return photo
