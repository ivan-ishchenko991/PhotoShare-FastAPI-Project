from sqlalchemy import Column, Integer, String, Boolean, func, Table, Text, ForeignKey
import enum
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql.sqltypes import Enum
from datetime import datetime

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
    roles = Column(Enum("User", "Moderator", "Administrator", name="user_roles"), default="User")
    refresh_token = Column(String(255), nullable=True)
    confirmed_email = Column(Boolean, default=False)
    comments = relationship("Comment", backref="users")
    tags = relationship("Tag", backref="users")
    photos = relationship("Photo", backref="user")


photo_2_tag = Table("photo_2_tag", Base.metadata,
                    Column('id', Integer, primary_key=True),
                    Column('photo_id', Integer, ForeignKey('photos.id', ondelete='CASCADE')),
                    Column('tag_id', Integer, ForeignKey('tags.id', ondelete='CASCADE')),
                    )


class Photo(Base):
    __tablename__ = "photos"
    id = Column(Integer, primary_key=True)
    image_url = Column(String(300))
    description = Column(String(500), nullable=True)
    tags = relationship('Tag', secondary=photo_2_tag, backref='photos')
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now())
    # Зовнішній ключ для зв'язку з користувачем
    user_id = Column(Integer, ForeignKey("users.id", ondelete='CASCADE'), default=None)
    image_transform = Column(String(200), nullable=True)
    qr_transform = Column(String(200), nullable=True)
    public_id = Column(String(100), nullable=True)
    comments = relationship('Comment', backref="photos", cascade="all, delete-orphan")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, default=func.now())
    user_id = Column('user_id', ForeignKey('users.id', ondelete='CASCADE'), default=None)


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    photo_id = Column(Integer, ForeignKey("photos.id"))
