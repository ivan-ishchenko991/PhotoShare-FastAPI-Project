from datetime import datetime
from typing import List, Optional
from enum import Enum

from fastapi_filter.contrib.sqlalchemy import Filter
from pydantic import BaseModel, EmailStr, Field, constr, SecretStr, validator
from datetime import datetime

from src.database.models import Photo


class UserModel(BaseModel):
    username: str = Field(min_length=5, max_length=16)
    email: EmailStr
    password: str = Field(min_length=6, max_length=20)


class UserDb(BaseModel):
    id: int
    username: str
    email: EmailStr
    photos_count: Optional[int] = 0
    avatar: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    user: UserDb
    detail: str = "User successfully created"


class UserUpdate(BaseModel):
    email: EmailStr
    username: constr(min_length=3, max_length=50)
    password: SecretStr


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr


class Role(str, Enum):
    User = "User"
    Moderator = "Moderator"
    Administrator = "Administrator"


class AdminUserPatch(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[constr(min_length=3, max_length=50)] = None
    password: Optional[SecretStr] = None
    is_active: Optional[bool] = None


class TagBase(BaseModel):
    title: str = Field(max_length=50)


class TagModel(TagBase):
    pass

    class Config:
        from_attributes = True


class TagResponse(TagBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PhotoCreate(BaseModel):
    description: str
    tags: List[str] = []


class PhotoUpdate(BaseModel):
    description: str
    tags: List[str] = []


# Models for transformation photos
class PhotoTransform(BaseModel):
    id: int
    image_transform: str
    detail: str = "Image successfully transform"


class PhotoLinkTransform(BaseModel):
    image_transform: str
    qr_transform: str


class TransformCircleModel(BaseModel):
    use_filter: bool = False
    height: int = Field(ge=0, default=400)
    width: int = Field(ge=0, default=400)


class TransformEffectModel(BaseModel):
    use_filter: bool = False
    art_audrey: bool = False
    art_zorro: bool = False
    cartoonify: bool = False
    blur: bool = False


class TransformResizeModel(BaseModel):
    use_filter: bool = False
    crop: bool = False
    fill: bool = False
    height: int = Field(ge=0, default=400)
    width: int = Field(ge=0, default=400)


class TransformTextModel(BaseModel):
    use_filter: bool = False
    font_size: int = Field(ge=0, default=70)
    text: str = Field(max_length=100, default="")


class TransformRotateModel(BaseModel):
    use_filter: bool = False
    width: int = Field(ge=0, default=400)
    degree: int = Field(ge=-360, le=360, default=45)


class TransformBodyModel(BaseModel):
    circle: TransformCircleModel
    effect: TransformEffectModel
    resize: TransformResizeModel
    text: TransformTextModel
    rotate: TransformRotateModel


# Model for filtering result
class PhotoFilter(Filter):
    order_by: Optional[list[str]] = None

    class Constants(Filter.Constants):
        model = Photo
        search_model_fields = ["description", "created_at", "updated_at"]


class PhotoResponse(BaseModel):
    id: int
    image_url: str
    qr_transform: Optional[str]
    likes: int
    description: str
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse]


class PhotoListResponse(BaseModel):
    photos: List[PhotoResponse]


# schemas for function only "get_all_photos"
class PhotoResponseAll(BaseModel):
    id: int
    image_url: str
    qr_transform: Optional[str]
    likes: Optional[int] = 0
    description: str
    photo_owner: str
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse]


class PhotoListResponseAll(BaseModel):
    photos: List[PhotoResponseAll]


# end

class CommentBase(BaseModel):
    text: str = Field(max_length=500)


class CommentModel(CommentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    user_id: int
    photo_id: int

    class Config:
        from_attributes = True


class CommentIn(BaseModel):
    text: str

    @validator("text")
    def set_updated_at(cls, v, values):
        values["updated_at"] = datetime.now()
        return v
