from typing import List, Optional 
from libgravatar import Gravatar 
from sqlalchemy.orm import Session 
from src.database.models import User,Roles,Photo
from src.schemas import UserModel 


async def get_user_by_email(email: str, db: Session) -> User: 
    """
    The get_user_by_email function takes in an email and a database session,
    and returns the user associated with that email. If no such user exists,
    it will return None.

    :param email: str: Specify the email of the user we want to get from our database
    :param db: Session: Pass the database session to the function
    :return: The first user with the given email address
    """
    return db.query(User).filter(User.email == email).first()


async def create_user(body: UserModel, db: Session) -> User: 
    """
    The create_user function creates a new user in the database.

    :param body: UserModel: Get the information from the user
    :param db: Session: Create a database session
    :return: A user object
    """
    avatar = None
    try: 
        g = Gravatar(body.email) 
        avatar = g.get_image() 
    except Exception as e: 
        print(e) 
    new_user = User(**body.dict(), avatar=avatar) 
    if not db.query(User).count(): 
        new_user.roles = "Administrator" 
    else: 
        new_user.roles = "User" 
    db.add(new_user) 
    db.commit() 
    db.refresh(new_user) 
    return new_user 


async def update_avatar(email, url: str, db: Session) -> User: 
    """
    The update_avatar function updates the avatar of a user.

    :param email: Find the user in the database
    :param url: str: Specify the type of data that is expected to be passed into the function
    :param db: Session: Pass the database session to the function
    :return: The updated user object
    """
    user = await get_user_by_email(email, db)
    user.avatar = url 
    db.commit() 
    return user 


async def update_token(user: User, token: str | None, db: Session) -> None: 
    """
    The update_token function updates the refresh token for a user in the database.

    :param user: User: Pass the user object to the function
    :param token: str | None: Update the user's refresh token
    :param db: Session: Pass the database session to the function
    :return: None
    """
    user.refresh_token = token
    db.commit() 


async def confirmed_email(email: str, db: Session) -> None: 
    """
    The confirmed_email function takes in an email and a database session, then returns None.
    It sets the confirmed_email field of the user with that email to True.

    :param email: str: Pass the email address of the user to be updated
    :param db: Session: Pass the database session to the function
    :return: None
    """
    user = await get_user_by_email(email, db)
    user.confirmed_email = True 
    db.commit() 


async def block_user(user_email:str, db: Session) -> None: 
    """
    The block_user function takes in a user_email and db as parameters.
    It then calls the get_user_by_email function to retrieve the user object from the database.
    The is_banned attribute of that object is set to True, and then committed to the database.

    :param user_email:str: Get the user's email address
    :param db: Session: Pass in the database session
    :return: None
    """
    result = await get_user_by_email(user_email,db)
    result.is_banned = True
    db.commit()         
    db.refresh(result)

async def change_role(user_email:str,role:Roles, db:Session):
    user = await get_user_by_email(user_email,db)
    if user.roles != Roles.admin:
        user.roles = role
        db.commit()
        db.refresh(user)
        return "OK"
    else:
        return "NOT OK"
    
async def put_a_like(photo_id:int,current_user, db:Session):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if current_user.email not in photo.who_liked:
        photo.likes += 1
        photo.who_liked += f"{current_user.email},"
        db.commit()
        db.refresh(photo)
        return "OK"
    else:
        return "NOT OK"
    
async def dislike(photo_id:int,current_user, db:Session):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if current_user.email in photo.who_liked:
        photo.likes -= 1
        photo.who_liked = photo.who_liked.replace(f"{current_user.email},", "")
        db.commit()
        db.refresh(photo)
        return "OK"
    else:
        return "NOT OK"
    
async  def delete_like_admin_moder(user_email:str,photo_id:int, db:Session):
    photo = db.query(Photo).filter(Photo.id == photo_id).first()
    if user_email not in photo.who_liked:
        return "NOT OK"
    else:
        photo.likes -= 1
        photo.who_liked = photo.who_liked.replace(f"{user_email},", "")
        db.commit()
        db.refresh(photo)
        return "OK"