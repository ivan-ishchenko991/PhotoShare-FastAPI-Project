from typing import Any, List
from fastapi import Depends, HTTPException, status
from src.database.models import User
from src.services.auth import auth_service


class RoleChecker:
    def __init__(self, allowed_roles: List[str]):
        """
        The __init__ function is called when the class is instantiated.
        It sets up the instance of the class, and allows us to pass in parameters that will be used by other functions in our class.
        In this case, we are passing a list of strings representing roles that are allowed to use this command.

        :param self: Represent the instance of the class
        :param allowed_roles: List[str]: Define the allowed roles for a user
        :return: An object of the class
        """
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(auth_service.get_current_user)):
        """
        The __call__ function is a decorator that allows us to use the class as a function.
        It takes in the current_user and checks if it's role is allowed to access this endpoint.
        If not, it raises an HTTPException with status code 403 (Forbidden)

        :param self: Refer to the current instance of a class
        :param current_user: User: Get the user object from the auth_service
        :return: A function that can be used to decorate a route
        """
        if current_user.roles not in self.allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Operation forbidden')
