from fastapi import APIRouter, HTTPException, Depends, Path, Query, status, Security
from fastapi.security import HTTPAuthorizationCredentials

from src.database.db import get_db
from src.routes.auth import security
from src.schemas import UserUpdateModel, UserDeleteResponse, UserUpdateResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.repository import users as repository_users
from src.services.auth import auth_service

router = APIRouter(prefix="/users", tags=["users"])


@router.put("/", response_model=UserUpdateResponse)
async def update_user(body: UserUpdateModel, credentials: HTTPAuthorizationCredentials = Security(security),
                      db: AsyncSession = Depends(get_db)):
    token = credentials.credentials
    autorised_user = await auth_service.authorised_user(token, db)
    if not autorised_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    result = await repository_users.update_user(body, db, autorised_user)
    return result



@router.delete("/", response_model=UserDeleteResponse)
async def delete_user(credentials: HTTPAuthorizationCredentials = Security(security), db: AsyncSession = Depends(get_db)):
    token = credentials.credentials
    autorised_user = await auth_service.authorised_user(token, db)
    if not autorised_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    user = await repository_users.remove_user(autorised_user, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="NOT FOUND",
        )
    return user
