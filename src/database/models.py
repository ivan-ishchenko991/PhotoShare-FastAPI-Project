import enum
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql.sqltypes import Enum


Base = declarative_base()

class Roles(str, enum.Enum):
    admin = "Administrator"
    moderator = "Moderator"
    user = "User"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(250), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    created_at = Column('crated_at', DateTime, default=func.now())
    avatar = Column(String(255), nullable=True)
    roles = Column(Enum("User", "Moderator", "Administrator",name="user_roles"), default="User")
    refresh_token = Column(String(255), nullable=True)
    confirmed_email = Column(Boolean, default=False)


