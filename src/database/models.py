from sqlalchemy import Column, Integer, String, Boolean, func, Table,Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.sqltypes import Enum


Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    email = Column(String(250), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    created_at = Column('crated_at', DateTime, default=func.now())
    avatar = Column(String(255), nullable=True)
    refresh_token = Column(String(255), nullable=True)
    confirmed_email = Column(Boolean, default=False)


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
    # Зв'язок з користувачем
    user = relationship("User", back_populates="photos")
    image_transform = Column(String(200), nullable=True)
    qr_transform = Column(String(200), nullable=True)
    public_id = Column(String(100), nullable=True)
    comment = relationship('Comment', backref="photos", cascade="all, delete-orphan")