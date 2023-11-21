import unittest
from unittest.mock import MagicMock, Mock, patch

import cloudinary
from fastapi import UploadFile
from sqlalchemy.orm import Session

from src.conf.config import settings
from src.database.models import Photo, User
from src.schemas import PhotoResponse, PhotoResponseAll, UserResponse, PhotoCreate, PhotoUpdate, TagResponse
from src.repository.photos import (
    get_all_photos,
    get_top_photos,
    get_user_photos,
    get_user_photo_by_id,
    get_public_id_from_image_url,
    update_user_photo,
    create_user_photo,
    delete_user_photo,
    search_photos,
)


class TestPhotos(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=1, roles="Administrator")
        self.photo = MagicMock(spec=PhotoCreate(
            description="testing",
            tags=["testing", "tag"]
        ))
        self.photo_update = MagicMock(spec=PhotoUpdate(
            description="testing update",
            tags=["testing"]
        ))
        self.image = Mock(spec=UploadFile)
        self.image.file = Mock()

    async def test_get_all_photos(self):
        photos = [PhotoResponseAll(), PhotoResponseAll(), PhotoResponseAll()]
        self.session.query().join().options().offset().limit().all.return_value = photos
        result = await get_all_photos(skip=0, limit=100, db=self.session)
        self.assertEqual(result, photos)

    async def test_get_top_photos(self):
        photos = [Photo(), Photo(), Photo()]
        self.session.query().filter().all.return_value = photos
        result = await get_top_photos(skip=0, limit=100, db=self.session)
        self.assertEqual(result, photos)

    async def test_get_user_photos(self):
        photos = [
            PhotoResponse(
                id=1,
                image_url="https://example.com/image.jpg",
                qr_transform="https://example.com/qr_transform.jpg",
                likes=10,
                description="Photo description",
                created_at="2023-11-01T12:00:00",
                updated_at="2023-11-01T12:00:00",
                tags=[TagResponse(id=1, title="Tag 1", created_at="2023-11-01T12:00:00")]
            ),
            PhotoResponse(
                id=2,
                image_url="https://example.com/image2.jpg",
                qr_transform="https://example.com/qr_transform2.jpg",
                likes=15,
                description="Another photo description",
                created_at="2023-11-02T12:00:00",
                updated_at="2023-11-02T12:00:00",
                tags=[TagResponse(id=2, title="Tag 2", created_at="2023-11-02T12:00:00")]
            ),
        ]
        self.session.query().filter().offset().limit().all.return_value = photos
        result = await get_user_photos(user_id=1, skip=0, limit=100, db=self.session)
        self.assertEqual(result, photos)

    async def test_search_photos(self):
        photos = [Photo(), Photo(), Photo()]
        self.session.query().join().join().order_by().filter().all.return_value = photos
        result = await search_photos(description="string", tag="string", user="string", is_admin=True, db=self.session)
        self.assertEqual(result, photos)

    async def test_search_photos_not_found(self):
        self.session.query().join().join().order_by().filter().all.return_value = None
        result = await search_photos(description="string", tag="string", user="string", is_admin=True, db=self.session)
        self.assertIsNone(result)

    @patch('src.repository.photos.init_cloudinary')
    async def test_create_user_photo(self, mock_init_cloudinary):
        mock_init_cloudinary.return_value = None

        cloudinary.config(
            cloud_name=settings.cloudinary_name,
            api_key=settings.cloudinary_api_key,
            api_secret=settings.cloudinary_api_secret,
            # secure=True
        )

        photo_create_data = {
            "description": "Test Description",
            "tags": ["tag1", "tag2"],
        }
        mock_photo_create = MagicMock()
        mock_photo_create.dict.return_value = photo_create_data

        mock_upload_file = MagicMock()
        mock_upload_file.file.read.return_value = b"Mocked image content"

        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.id = 1

        mock_session = MagicMock()
        mock_db_photo = MagicMock()
        mock_db_photo.__dict__ = {
            "id": 1,
            "image_url": "https://example.com/image.jpg",
        }
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        result = await create_user_photo(mock_photo_create, mock_upload_file, mock_user, mock_session)

        self.assertIsNotNone(result)
        self.assertEqual(result.id, mock_db_photo.__dict__["id"])

    async def test_get_user_photo_by_id(self):
        photo = PhotoResponse(
                id=1,
                image_url="https://example.com/image.jpg",
                qr_transform="https://example.com/qr_transform.jpg",
                likes=10,
                description="Photo description",
                created_at="2023-11-01T12:00:00",
                updated_at="2023-11-01T12:00:00",
                tags=[TagResponse(id=1, title="Tag 1", created_at="2023-11-01T12:00:00")]
            )
        self.session.query().filter().first.return_value = photo
        result = await get_user_photo_by_id(photo_id=1, db=self.session, current_user=self.user)
        self.assertEqual(result, photo)

    async def test_get_user_photo_by_id_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await get_user_photo_by_id(photo_id=1, db=self.session, current_user=self.user)
        self.assertIsNone(result)

    async def test_update_user_photo(self):
        photo = Photo(
            id=1,
            image_url="https://example.com/image.jpg",
            qr_transform="https://example.com/qr_transform.jpg",
            likes=10,
            description="Photo description",
            created_at="2023-11-01T12:00:00",
            updated_at="2023-11-01T12:00:00",
        )
        photo_update = PhotoUpdate(
            description="Photo updated description",
            tags=["Updated tag"]
        )
        self.session.query().filter().first.return_value = photo
        result = await update_user_photo(
            photo=photo,
            updated_photo=photo_update,
            current_user=self.user,
            db=self.session
        )
        self.assertEqual(result.description, "testing update")
        self.assertEqual(result.tags, ["testing"])

    async def test_delete_user_photo(self):
        photo = Photo()
        self.session.query().filter().first.return_value = photo
        result = await delete_user_photo(photo_id=1, user_id=1, is_admin=True, db=self.session)
        self.assertEqual(result, photo)

    async def test_delete_user_photo_not_found(self):
        photo = Photo()
        self.session.query().filter().first.return_value = None
        result = await delete_user_photo(photo_id=1, user_id=1, is_admin=True, db=self.session)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
