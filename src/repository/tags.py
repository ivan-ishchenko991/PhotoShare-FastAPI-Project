from typing import List

from sqlalchemy.orm import Session

from src.database.models import Tag, User
from src.schemas import TagBase


async def create_tag(body: TagBase,
                     db: Session,
                     user: User
                     ) -> Tag | None:
    tag = db.query(Tag).filter(Tag.title == body.title).first()
    if not tag:
        tag = Tag(
            title=body.title,
            user_id=user.id
        )
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag
    else:
        return None


async def get_my_tags(skip: int,
                      limit: int,
                      db: Session,
                      user: User) -> List[Tag]:
    return db.query(Tag).filter(Tag.user_id == user.id).offset(skip).limit(limit).all()


async def get_all_tags(skip: int,
                       limit: int,
                       db: Session
                       ) -> List[Tag]:
    return db.query(Tag).offset(skip).limit(limit).all()


async def get_tag_by_id(tag_id: int,
                        db: Session
                        ) -> Tag:
    return db.query(Tag).filter(Tag.id == tag_id).first()


async def update_tag(tag_id: int,
                     body: TagBase,
                     db: Session
                     ) -> Tag | None:
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if tag:
        tag.title = body.title
        db.commit()
    return tag


async def remove_tag(tag_id: int,
                     db: Session
                     ) -> Tag | None:
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if tag:
        db.delete(tag)
        db.commit()
    return tag
