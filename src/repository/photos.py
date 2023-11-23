from datetime import datetime
from typing import List
from fastapi import UploadFile
import cloudinary
from cloudinary.uploader import upload
from cloudinary.uploader import destroy
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session, joinedload
from fastapi.exceptions import HTTPException

from src.database.models import Photo, User, Tag, Comment, photo_2_tag
from src.conf.config import settings
from src.schemas import PhotoCreate, PhotoUpdate, PhotoListResponse, TagResponse, PhotoResponse, PhotoResponseAll


def init_cloudinary():
    """
    The init_cloudinary function is used to initialize the cloudinary library with
    the settings from our Django project's settings.py file.

    :return: Nothing
    """
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )


async def get_all_photos(skip: int, limit: int, db: Session) -> List[Photo]:
    """
    The get_all_photos function returns a list of all photos in the database.
        Args:
            skip (int): The number of photos to skip before returning results.
            limit (int): The maximum number of photos to return.

    :param skip: int: Skip a certain number of photos
    :param limit: int: Limit the number of photos returned in a single request
    :param db: Session: Pass the database session to the function
    :return: A list of photoresponseall objects
    """
    photos = (
        db.query(Photo)
        .join(User)
        .options(joinedload(Photo.user))
        .offset(skip)
        .limit(limit)
        .all()
    )

    photos_with_username = [
        PhotoResponseAll(
            id=photo.id,
            image_url=photo.image_url,
            qr_transform=photo.qr_transform,
            likes=photo.likes,
            description=photo.description,
            photo_owner=photo.user.username,
            created_at=photo.created_at,
            updated_at=photo.updated_at,
            tags=photo.tags
        )
        for photo in photos
    ]

    return photos_with_username


async def get_top_photos(skip: int, limit: int, db: Session) -> List[Photo]:
    """
    The get_top_photos function returns a list of photos with the most likes.
        Args:
            skip (int): The number of photos to skip before returning results.
            limit (int): The maximum number of photos to return.

    :param skip: int: Skip a certain number of photos in the database
    :param limit: int: Limit the number of photos returned
    :param db: Session: Pass in the database session
    :return: A list of photos with the username of the owner
    """
    photos = (
        db.query(Photo)
        .join(User)
        .options(joinedload(Photo.user))
        .order_by(desc(Photo.likes))
        .offset(skip)
        .limit(limit)
        .all()
    )

    photos_with_username = [
        PhotoResponseAll(
            id=photo.id,
            image_url=photo.image_url,
            qr_transform=photo.qr_transform,
            likes=photo.likes,
            description=photo.description,
            photo_owner=photo.user.username,  
            created_at=photo.created_at,
            updated_at=photo.updated_at,
            tags=photo.tags
        )
        for photo in photos
    ]

    return photos_with_username


async def get_public_id_from_image_url(image_url: str) -> str:
    """
    The get_public_id_from_image_url function takes a Cloudinary image URL as input and returns the public ID of that
    image. The public ID is the unique identifier for an image in your Cloudinary account. It is used to reference
    images in all API calls, including when you upload them.

    :param image_url: str: Specify the image url that is passed into the function
    :return: The public id of the image
    """
    parts = image_url.split("/")
    public_id = parts[-1]
    public_id = public_id.replace('%40', '@')
    return public_id


async def create_user_photo(photo: PhotoCreate, image: UploadFile, current_user: User, db: Session) -> PhotoResponse:
    """
    The create_user_photo function creates a new photo in the database. Args: photo (PhotoCreate): The PhotoCreate
    object containing the data to create a new Photo. image (UploadFile): The UploadFile object containing the image
    file to upload and associate with this Photo. current_user (User): The User object representing who is making
    this request, used for authorization purposes.

    :param photo: PhotoCreate: Create a new photo object
    :param image: UploadFile: Get the image file from the request body
    :param current_user: User: Get the user's id from the database
    :param db: Session: Access the database
    :return: The photoresponse object
    """
    init_cloudinary()
    # Створення унікального public_id на основі поточного часу
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


async def get_user_photos(user_id: int, skip: int, limit: int, db: Session) -> list[PhotoResponse]:
    """
    The get_user_photos function returns a list of PhotoResponse objects. The function takes in the following
    parameters: user_id (int): The id of the user whose photos we want to retrieve. If None, all photos are returned.
    skip (int): The number of items to skip before returning results. Used for pagination purposes only. Defaults to
    0 if not specified by caller or is less than 0; otherwise, it is set equal to the value passed in by caller and
    used as-is without modification/validation checks on its value beyond that already performed above via Python's
    type system and default parameter values mechanism).


    :param user_id: int: Filter the photos by user_id
    :param skip: int: Skip the first n photos
    :param limit: int: Limit the number of photos returned
    :param db: Session: Pass the database session to the function
    :return: A list of photoresponse objects
    """
    photos_query = db.query(Photo)
    # Якщо user_id має значення None, не фільтруємо за user_id
    if user_id is not None:
        photos_query = photos_query.filter(Photo.user_id == user_id)
    photos = photos_query.offset(skip).limit(limit).all()

    return [PhotoResponse(
        id=photo.id,
        image_url=photo.image_url,
        qr_transform=photo.qr_transform,
        likes=photo.likes,
        description=photo.description,
        created_at=photo.created_at,
        updated_at=photo.updated_at,
        tags=[TagResponse(id=tag.id, title=tag.title, created_at=tag.created_at) for tag in photo.tags]
    ) for photo in photos]


async def get_user_photo_by_id(photo_id: int, db: Session, current_user: User) -> PhotoResponse:
    """
   The get_user_photo_by_id function returns a PhotoResponse object for the photo with the specified ID.

   :param photo_id: int: Specify the photo id
   :param db: Session: Access the database
   :param current_user: User: Check if the user is an administrator
   :return: A photo by id
   """
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
        likes=photo.likes,
        description=photo.description,
        created_at=photo.created_at,
        updated_at=photo.updated_at,
        tags=[TagResponse(id=tag.id, title=tag.title, created_at=tag.created_at) for tag in photo.tags]
    )


async def update_user_photo(photo: Photo, updated_photo: PhotoUpdate, current_user: User, db: Session) -> PhotoResponse:
    """
    The update_user_photo function updates a photo in the database. Args: photo (Photo): The Photo object to be
    updated. updated_photo (PhotoUpdate): The new data for the Photo object. current_user (User): The user who is
    updating the Photo object. This is used to ensure that only an owner of a given resource can update it,
    and not just anyone with access to this function/endpoint/route.

    :param photo: Photo: Get the photo object from the database
    :param updated_photo: PhotoUpdate: Pass the updated photo data to the function
    :param current_user: User: Check if the user is authorized to update the photo
    :param db: Session: Access the database
    :return: The updated photo
    """
    if updated_photo.description is not None:
        photo.description = updated_photo.description

    if updated_photo.tags:
        tag_objects = []
        for tag_name in updated_photo.tags:
            tag = db.query(Tag).filter(Tag.title == tag_name).first()
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
        likes=photo.likes,
        description=photo.description,
        created_at=photo.created_at,
        updated_at=photo.updated_at,
        tags=[TagResponse(id=tag.id, title=tag.title, created_at=tag.created_at) for tag in photo.tags]
    )


async def search_photos(description: str, tag: str, user: str, is_admin: bool, db: Session) -> list[Photo]:
    """
    The search_photos function searches for photos in the database.
        It takes a description, tag, and user as arguments. If all three are provided, it will search for photos with that
        description and tag by that user. If only two of the three are provided (description and tag or description and
        user), it will search for photos with that combination of attributes. If only one is provided (description or
        tag or username), it will search for all photos matching just that attribute.

    :param description: str: Search for photos with a specific description
    :param tag: str: Filter the photos by tag
    :param user: str: Filter photos by user
    :param is_admin: bool: Check if the user is an admin
    :param db: Session: Pass the database session to the function
    :return: A list of photos
    """
    if description and tag:
        photos = db.query(Photo).join(photo_2_tag).join(Tag).order_by(desc(Photo.created_at)).filter(
            and_(Photo.description == description, Tag.title == tag)
        ).all()
    elif description and (not tag):
        photos = db.query(Photo).order_by(desc(Photo.created_at)).filter(
            Photo.description == description
        ).all()
    elif tag and (not description):
        photos = db.query(Photo).join(photo_2_tag).join(Tag).order_by(desc(Photo.created_at)).filter(
            Tag.title == tag
        ).all()
    elif user and (not description) and (not tag):
        if not is_admin:
            raise HTTPException(status_code=403, detail="Permission denied")
        photos = db.query(Photo).join(User).order_by(desc(Photo.created_at)).filter(
            User.username == user
        ).all()
    else:
        photos = db.query(Photo).order_by(desc(Photo.created_at)).all()

    return photos


async def delete_user_photo(photo_id: int, user_id: int, is_admin: bool, db: Session):
    """
    The delete_user_photo function deletes a photo from the database and Cloudinary. Args: photo_id (int): The id of
    the photo to be deleted. user_id (int): The id of the user who is deleting this photo. This is used to check if
    they have permission to delete it or not. is_admin (bool): Whether or not this user has admin privileges,
    which would allow them to delete any photos regardless of ownership status.

    :param photo_id: int: Find the photo in the database
    :param user_id: int: Get the user's photos from the database
    :param is_admin: bool: Determine if the user is an admin or not
    :param db: Session: Access the database
    :return: The deleted photo
    """
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
