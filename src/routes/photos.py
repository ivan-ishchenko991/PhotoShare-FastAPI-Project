from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile, Query
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer

from src.schemas import (
    PhotoCreate,
    PhotoUpdate,
    PhotoResponse,
    PhotoListResponse,
    TagResponse, TransformBodyModel, PhotoTransform, PhotoLinkTransform, PhotoListResponseAll
)
from src.services.auth import auth_service
from src.database.connect import get_db
from src.database.models import Photo, User
from src.repository import photos as repository_photos
from src.repository import qr_code as qr
from src.services.photos import transform_image, create_link_transform_image

router = APIRouter(prefix='/photos', tags=["photos"])
security = HTTPBearer()


@router.get("/all_photos", response_model=PhotoListResponseAll)
async def get_all_photos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    photos = await repository_photos.get_all_photos(skip, limit, db)
    return {"photos": photos}

@router.get("/top_photos", response_model=PhotoListResponseAll)
async def get_top_photos(skip: int = 0, limit: int= 20, db: Session = Depends(get_db)):
    photos  = await repository_photos.get_top_photos(skip, limit,db)
    return {"photos": photos}

@router.post("/", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
async def create_user_photo(
        image: UploadFile = File(...),
        description: str = Form(...),
        tags: List[str] = Form([]),
        db: Session = Depends(get_db),
        current_user: User = Depends(auth_service.get_current_user),
        token: str = Depends(auth_service.oauth2_scheme),
):
    """
    The create_user_photo function creates a new photo for the current user.

    :param image: UploadFile: Upload the image file to the server
    :param description: str: Specify the description of the photo
    :param tags: List[str]: Create a list of tags
    :param db: Session: Pass the database session to the repository layer
    :param current_user: User: Get the current user
    :param token: str: Check if the token is blacklisted
    :param : Get the current user
    :return: A tuple of (photo, str)
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    if len(tags) > 5:
        raise HTTPException(status_code=400, detail="Too many tags provided")

    photo_data = PhotoCreate(description=description, tags=tags)
    return repository_photos.create_user_photo(photo_data, image, current_user, db)


@router.post("/create_qr_code", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
async def create_qr_code(photo_id: int,
                         current_user: User = Depends(auth_service.get_current_user),
                         db: Session = Depends(get_db),
                         token: str = Depends(auth_service.oauth2_scheme),
                         ):
    """
    The create_qr_code function creates a QR code for the photo with the given ID. The function requires that a valid
    token be passed in as an authorization header, and it will return an error if no such token is found or if the
    token is blacklisted. If no photo with the given ID exists, then this function will return a 404 Not Found error.

    :param photo_id: int: Get the photo from the database
    :param current_user: User: Get the user that is currently logged in
    :param db: Session: Access the database
    :param token: str: Check if the token is blacklisted
    :param : Get the photo id from the url
    :return: A photo object
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
    photo = await qr.make_qr_code_for_photo(photo_id, current_user, db)
    if photo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found")
    return photo


@router.get("/", response_model=PhotoListResponse)
async def get_user_photos(
        skip: int = 0,
        limit: int = 10,
        db: Session = Depends(get_db),
        current_user: User = Depends(auth_service.get_current_user),
        token: str = Depends(auth_service.oauth2_scheme),
):
    """
    The get_user_photos function returns a list of photos for the current user.
    The function takes in an optional skip and limit parameter to paginate through the results.


    :param skip: int: Specify the number of photos to skip
    :param limit: int: Set the number of photos to be returned
    :param db: Session: Get the database session
    :param current_user: User: Get the current user
    :param token: str: Check if the token is blacklisted
    :param : Specify the number of photos to skip
    :return: A list of photos for the current user
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
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
        token: str = Depends(auth_service.oauth2_scheme),
):
    """
    The get_user_photo_by_id function is used to get a specific photo by its id. The function takes the following
    parameters: - photo_id: int, required, unique identifier of the photo to be retrieved. - current_user: User
    object containing information about the user making this request (optional). This parameter is automatically
    passed in when using an access token with this endpoint. If no access token is provided or if it has expired,
    then current_user will not be populated and you will receive a 401 error response from FastAPI indicating that
    there was a problem with authentication. You can use Post

    :param photo_id: int: Specify the photo id
    :param current_user: User: Get the current user
    :param db: Session: Access the database
    :param token: str: Check if the token is blacklisted
    :param : Pass the photo id to the function
    :return: A photo by id
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
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
        qr_transform=photo.qr_transform,
        likes = photo.likes,
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
        token: str = Depends(auth_service.oauth2_scheme),
):
    """
    The update_user_photo function updates a photo in the database.
        The function takes an id of the photo to be updated, and a PhotoUpdate object containing
        information about what is to be updated. It then checks if the user has permission to update
        this particular photo (if they are an admin or if it's their own). If so, it calls on
        repository_photos' update_user_photo function which actually performs the update.

    :param photo_id: int: Specify the id of the photo to be deleted
    :param updated_photo: PhotoUpdate: Get the updated photo from the request body
    :param current_user: User: Get the user that is currently logged in
    :param db: Session: Get a database session
    :param token: str: Check if the token is blacklisted
    :param : Get the current user from the database
    :return: The updated photo object
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
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


@router.get("/search/", response_model=List[PhotoResponse])
async def search_photos(
    description: str = Query(None, description='Searching photos by description'),
    tag: str = Query(None, description='Searching photos by tags'),
    username: str = Query(None, description='Searching photos by username'),
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
):
    is_admin = "Administrator" in current_user.roles.split(",")

    photos = await repository_photos.search_photos(description, tag, username, is_admin, db)
    if (photos is None) or photos == []:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return photos


@router.delete("/{photo_id}", response_model=PhotoResponse)
async def delete_user_photo(
        photo_id: int,
        current_user: User = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db),
        token: str = Depends(auth_service.oauth2_scheme),
):
    """
    The delete_user_photo function deletes a photo from the database.

    :param photo_id: int: Specify the photo to be deleted
    :param current_user: User: Get the current user
    :param db: Session: Access the database
    :param token: str: Check if the token is blacklisted
    :param : Get the current user from the database
    :return: A dictionary with the following structure:
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
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
        "qr_transform": result.qr_transform,
        "description": result.description,
        "created_at": result.created_at,
        "updated_at": result.updated_at,
        "tags": result.tags
    }

    return response_data


@router.patch("/transformation/{photo_id}", response_model=PhotoTransform)
async def photo_transformation(
        photo_id: int,
        body: TransformBodyModel,
        current_user: User = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db),
        token: str = Depends(auth_service.oauth2_scheme),
):
    """
    The photo_transformation function is responsible for transforming the image. It takes in a photo_id,
    body and current_user as parameters. The photo_id parameter is used to find the image that needs to be
    transformed. The body parameter contains all of the transformation information needed to transform an image (
    e.g., rotation angle). The current user is used for authentication purposes.

    :param photo_id: int: Get the photo from the database by its id
    :param body: TransformBodyModel: Get the data from the request body
    :param current_user: User: Get the current user from the database
    :param db: Session: Get a database session
    :param token: str: Get the token from the header
    :param : Get the photo id
    :return: A dict with the id of the photo, a transformed image and a detail
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
    photo = await transform_image(photo_id, body, current_user, db)
    if photo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )
    if isinstance(photo, Photo):
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="You don't choose type transformation",
        )
    return {
        "id": photo_id,
        "image_transform": photo,
        "detail": "Your image successfully transform",
    }


@router.post("/create_link_for_transformation", response_model=PhotoLinkTransform)
async def create_link_for_image_transformation(
        photo_id: int,
        current_user: User = Depends(auth_service.get_current_user),
        db: Session = Depends(get_db),
        token: str = Depends(auth_service.oauth2_scheme),
):
    """
    The create_link_for_image_transformation function creates a link for the image transformation.
        The function takes in an integer photo_id, which is the id of the photo to be transformed.
        It also takes in a current_user object, which is used to determine if the user has access to this resource.
        It also takes in a db Session object, which allows us to interact with our database and perform queries on it.
        Finally it takes in token string that will be used for authentication purposes.

    :param photo_id: int: Get the photo id from the request
    :param current_user: User: Get the current user from the database
    :param db: Session: Get the database session
    :param token: str: Check if the token is blacklisted
    :param : Get the photo id from the url
    :return: The link for the image transformation
    """
    if await auth_service.is_token_blacklisted(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is blacklisted")
    result = await create_link_transform_image(photo_id, current_user, db)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )
    return result
