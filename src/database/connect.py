from sqlalchemy.engine import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.conf.config import settings
from src.database.models import Base

SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
