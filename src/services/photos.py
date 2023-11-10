import qrcode
import cloudinary
import cloudinary.uploader
import cloudinary.api
from sqlalchemy.orm import Session
from sqlalchemy import and_
from PIL import Image
from io import BytesIO

from src.schemas import TransformBodyModel
from src.database.models import User, Photo
from src.repository.photos import init_cloudinary


async def transform_image(photo_id: int, body: TransformBodyModel, user: User, db: Session) -> Photo | None:
    init_cloudinary()
    photo = db.query(Photo).filter(and_(Photo.id == photo_id, Photo.user_id == user.id)).first()
    if photo:
        transformation = []

        if body.circle.use_filter and body.circle.height and body.circle.width:
            trans_list = [{'gravity': "face", 'height': f"{body.circle.height}", 'width': f"{body.circle.width}",
                           'crop': "thumb"},
                          {'radius': "max"}]
            [transformation.append(elem) for elem in trans_list]

        if body.effect.use_filter:
            effect = ""
            if body.effect.art_audrey:
                effect = "art:audrey"
            if body.effect.art_zorro:
                effect = "art:zorro"
            if body.effect.blur:
                effect = "blur:300"
            if body.effect.cartoonify:
                effect = "cartoonify"
            if effect:
                transformation.append({"effect": f"{effect}"})

        if body.resize.use_filter and body.resize.height and body.resize.height:
            crop = ""
            if body.resize.crop:
                crop = "crop"
            if body.resize.fill:
                crop = "fill"
            if crop:
                trans_list = [{"gravity": "auto", 'height': f"{body.resize.height}", 'width': f"{body.resize.width}",
                               'crop': f"{crop}"}]
                [transformation.append(elem) for elem in trans_list]

        if body.text.use_filter and body.text.font_size and body.text.text:
            trans_list = [{'color': "#FFFF00",
                           'overlay': {'font_family': "Times", 'font_size': f"{body.text.font_size}",
                                       'font_weight': "bold", 'text': f"{body.text.text}"}},
                          {'flags': "layer_apply", 'gravity': "south", 'y': 20}]
            [transformation.append(elem) for elem in trans_list]

        if body.rotate.use_filter and body.rotate.width and body.rotate.degree:
            trans_list = [{'width': f"{body.rotate.width}", 'crop': "scale"}, {'angle': "vflip"},
                          {'angle': f"{body.rotate.degree}"}]
            [transformation.append(elem) for elem in trans_list]

        if transformation:
            trans_image = cloudinary.CloudinaryImage(photo.public_id, format="png").build_url(
                transformation=transformation
            )
            cloudinary.uploader.upload(trans_image, public_id=photo.public_id, folder="PhotoshareApp_tr")
            photo.image_transform = trans_image
            db.commit()
            return photo.image_transform
        else:
            return photo


async def create_link_transform_image(photo_id: int, user: User, db: Session) -> str | None:
    init_cloudinary()
    photo = db.query(Photo).filter(and_(Photo.id == photo_id, Photo.user_id == user.id)).first()
    if photo:
        if photo.image_transform is not None:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(photo.image_transform)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")

            img_bytes = BytesIO()
            qr_img.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            qr = cloudinary.uploader.upload(img_bytes, public_id=photo.public_id + '_qr', folder="PhotoshareApp_tr")
            qr_url = cloudinary.CloudinaryImage("PhotoshareApp_tr/" + photo.public_id + '_qr', format="png").build_url(
                width=250, height=250, crop='fill', version=qr.get('version'))
            photo.qr_transform = qr_url
            db.commit()
            return {"image_transform": photo.image_transform, "qr_transform": photo.qr_transform}
