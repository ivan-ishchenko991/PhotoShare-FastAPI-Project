from fastapi import APIRouter, HTTPException, Depends, status, Security, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.database.connect import get_db
from src.schemas import UserModel, UserResponse, TokenModel, RequestEmail
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.services.email import send_email

router = APIRouter(prefix='/auth', tags=["auth"])
security = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    """
    The signup function creates a new user in the database.
        It takes in a UserModel object, which is validated by pydantic.
        If the email already exists, it will return an HTTP 409 error code (conflict).
        Otherwise, it will create a new user and send them an email to verify their account.

    :param body: UserModel: Get the user's email and password
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the application
    :param db: Session: Get a database session
    :return: A dict, so we need to specify the return type
    """
    exist_user = await repository_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_users.create_user(body, db)
    background_tasks.add_task(send_email, new_user.email, new_user.username, request.base_url)
    return {"user": new_user, "detail": "User successfully created"}


@router.post("/login", response_model=TokenModel)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    The login function is used to authenticate a user.
        It takes in the email and password of the user, verifies that they are correct,
        and returns an access token if successful.

    :param body: OAuth2PasswordRequestForm: Get the username and password from the request body
    :param db: Session: Get the database session
    :return: A dict with the access and refresh token
    """
    user = await repository_users.get_user_by_email(body.username, db)
    if user.is_banned:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is banned")
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email")
    if not user.confirmed_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not confirmed")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(token: str = Depends(auth_service.oauth2_scheme)):
    """
    The logout function is used to logout a user.

    :param token: str: Get the token from the request header
    :return: A dict with a message
    """
    await auth_service.logout(token)
    return {"message": "Successfully logged out"}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    The confirmed_email function is used to confirm a user's email address.
        It takes the token from the URL and uses it to get the user's email address.
        The function then checks if there is a user with that email in our database,
        and if not, returns an error message. If there is such a user, we check whether
        their account has already been confirmed or not; if it has been confirmed already,
        we return an appropriate message; otherwise we update their account status in our database.

    :param token: str: Get the token from the url
    :param db: Session: Get the database session from the dependency
    :return: A message indicating that the email has already been confirmed
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    if user.confirmed_email:
        return {"message": "Your email is already confirmed"}
    await repository_users.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: Session = Depends(get_db)):
    """
    The request_email function is used to send an email to the user with a link that will allow them
    to confirm their email address. The function takes in a RequestEmail object, which contains the
    email of the user who wants to confirm their account. It then checks if there is already a confirmed
    account associated with that email address, and if so returns an error message saying as much. If not, it sends
    an email containing a confirmation link.

    :param body: RequestEmail: Get the email from the request body
    :param background_tasks: BackgroundTasks: Add a task to the background tasks queue
    :param request: Request: Get the base url of the server
    :param db: Session: Get the database session
    :return: A message that the user can check their email for confirmation
    """
    user = await repository_users.get_user_by_email(body.email, db)

    if user.confirmed_email:
        return {"message": "Your email is already confirmed"}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, request.base_url)
    return {"message": "Check your email for confirmation."}


@router.get('/refresh_token', response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    """
    The refresh_token function is used to refresh the access token.
        The function takes in a refresh token and returns an access_token, a new refresh_token, and the type of token.
        If the user's current refresh_token does not match what was passed into this function then it will return an error.

    :param credentials: HTTPAuthorizationCredentials: Get the token from the request header
    :param db: Session: Get the database session
    :return: A dictionary with the access_token, refresh_token and token_type
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_users.update_token(user, refresh_token, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
