import qrcode
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.database.models import User, Photo
import cloudinary.uploader
from io import BytesIO
from src.conf.config import settings


async def make_qr_code_for_photo(photo_id: int, current_user: User, db: Session):
    """
    The make_qr_code_for_photo function takes in a photo_id, current_user, and db. It then uses the qrcode library to
    create a QR code for the photo with that id. The QR code is uploaded to Cloudinary using cloudinary's uploader
    function and saved as an image with the same public id as the original image but appended with '_qr'. The url of
    this new qr transform is then added to the Photo object in our database.

    :param photo_id: int: Identify the photo to be transformed
    :param current_user: User: Ensure that the user is logged in and can only access their own photos
    :param db: Session: Connect to the database
    :return: A photo object with the qr_transform attribute set to the url of
    """
    cloudinary.config(
        cloud_name=settings.cloudinary_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret)

    photo = db.query(Photo).filter(and_(Photo.id == photo_id, Photo.user_id == current_user.id)).first()
    if photo:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        qr.add_data(photo.image_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        new_qr = cloudinary.uploader.upload(img_bytes, public_id=photo.public_id + '_qr', folder="PhotoshareApp_qrcode",
                                            overwrite=True)
        qr_url = cloudinary.CloudinaryImage("PhotoshareApp_qrcode/" + photo.public_id + '_qr', format="png").build_url(
            width=250, height=250, crop='fill', version=new_qr.get('version'))
        photo.qr_transform = qr_url
        db.commit()
        return photo
