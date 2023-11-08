from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, constr, SecretStr, validator
from datetime import datetime


class UserModel(BaseModel):
    username: str = Field(min_length=5, max_length=16)
    email: EmailStr
    password: str = Field(min_length=6, max_length=20)


class UserDb(BaseModel):
    id: int
    username: str
    email: EmailStr
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


class PhotoResponse(BaseModel):
    id: int
    image_url: str
    description: str
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse]


class PhotoListResponse(BaseModel):
    photos: List[PhotoResponse]


class CommentBase(BaseModel):
    text: str = Field(max_length=500)


class CommentModel(CommentBase):
    id: int
    created_at: datetime
    updated_at: datetime
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

class RatingCreate(BaseModel):
    value: int
