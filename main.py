import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session, sessionmaker
# from fastapi_limiter import FastAPILimiter

from src.conf.config import settings
from src.database.connect import get_db
from src.routes import user, auth, photos, tags, comments, rating

app = FastAPI()

SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(photo.router, prefix="/photos", tags=["photos"])
app.include_router(rating.router, prefix="/ratings", tags=["ratings"])

origins = [
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Welcome to PhotoShare!"}


@app.get("/api/healthchecker")
def healthchecker(db: Session = Depends(get_db)):
    try:
        # Make request
        result = db.execute(text("SELECT 1")).fetchone()
        print(result)
        if result is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail="Database is not configured correctly")
        return {"message": "Welcome to PhotoShare!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Error connecting to the database")


app.include_router(auth.router, prefix='/api')
app.include_router(photos.router, prefix='/api')
app.include_router(tags.router, prefix='/api')
app.include_router(comments.router, prefix='/api')

if __name__ == '__main__':
    uvicorn.run(app="main:app", reload=True)
