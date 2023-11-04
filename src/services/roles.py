from typing import Any, List
from fastapi import Depends, HTTPException, status
from src.database.models import User
from src.services.auth import auth_service

class RoleChecker:
    def __init__(self,allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User=Depends(auth_service.get_current_user)):
        if current_user.roles not in self.allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Operation forbidden')
                 
