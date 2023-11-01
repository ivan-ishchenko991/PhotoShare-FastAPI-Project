from sqlalchemy.engine import create_engine
from sqlalchemy.orm import sessionmaker

from src.conf.config import settings

url_to_db = SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url


engine = create_engine(url_to_db, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
