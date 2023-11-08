from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.database.connect import get_db
from src.repository import ratings as repository_ratings
from src.repository.ratings import (create_rating, get_ratings_by_photo_id, get_rating_by_user_photo,
                                   update_rating, delete_rating)
from src.database.models import Rating, User
from src.schemas import RatingBase, RatingModel
from src.services.auth import auth_service

@app.post("/ratings/", response_model=Rating)
def create_rating(rating: RatingCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing_rating = db.query(Rating).filter(
        Rating.user_id == current_user.id, Rating.photo_id == rating.photo_id
    ).first()
    if existing_rating:
        raise HTTPException(status_code=400, detail="Already rated this photo")
    return create_rating(db, rating, current_user)

@app.delete("/ratings/{rating_id}", response_model=Rating)
def delete_rating(rating_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rating = db.query(Rating).filter(Rating.id == rating_id).first()
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    if rating.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this rating")
    return remove_rating(db, rating_id)
