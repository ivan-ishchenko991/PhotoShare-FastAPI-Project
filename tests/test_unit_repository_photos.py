import unittest
from unittest.mock import MagicMock, Mock, patch, AsyncMock

import cloudinary
from fastapi import UploadFile
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from src.conf.config import settings
from src.database.models import Photo, User, Tag
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
        self.photo_response_all = [PhotoResponseAll(
                id=1,
                image_url="https://example.com/image.jpg",
                qr_transform="https://example.com/qr_transform.jpg",
                likes=10,
                description="Photo description",
                photo_owner="test owner",
                created_at="2023-11-01T12:00:00",
                updated_at="2023-11-01T12:00:00",
                tags=[TagResponse(id=1, title="Tag 1", created_at="2023-11-01T12:00:00")]
            ), PhotoResponseAll(
                id=2,
                image_url="https://example.com/image.jpg",
                qr_transform="https://example.com/qr_transform.jpg",
                likes=10,
                description="Photo description",
                photo_owner="test owner",
                created_at="2023-11-01T12:00:00",
                updated_at="2023-11-01T12:00:00",
                tags=[TagResponse(id=1, title="Tag 1", created_at="2023-11-01T12:00:00")]
            ), PhotoResponseAll(
                id=3,
                image_url="https://example.com/image.jpg",
                qr_transform="https://example.com/qr_transform.jpg",
                likes=10,
                description="Photo description",
                photo_owner="test owner",
                created_at="2023-11-01T12:00:00",
                updated_at="2023-11-01T12:00:00",
                tags=[TagResponse(id=1, title="Tag 1", created_at="2023-11-01T12:00:00")]
            )]

    async def test_get_all_photos(self):
        photos = self.photo_response_all

        self.session.query(Photo).join(User).options(joinedload(Photo.user)).offset(0).limit(100).all.return_value = photos
        result = await get_all_photos(skip=0, limit=100, db=self.session)
        self.assertEqual(result, photos)

    async def test_get_top_photos(self):
        photos = self.photo_response_all
        self.session.query().join(User).options(joinedload(Photo.user)).order_by(desc(Photo.likes)).offset().limit().all.return_value = photos
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

    @patch('src.repository.photos.cloudinary.uploader.upload')
    @patch('src.repository.photos.cloudinary.CloudinaryImage')
    @patch('src.repository.photos.init_cloudinary')
    async def test_create_user_photo(self, mock_init_cloudinary, mock_cloudinary_image, mock_cloudinary_uploader_upload):
        # Mocking the necessary data
        mock_photo_create = self.photo
        mock_upload_file = self.image
        mock_current_user = self.user
        mock_db_session = self.session

        # Mocking the current timestamp
        mock_timestamp = 1637869200.0  # Replace this with your desired timestamp

        # Mocking Cloudinary behavior
        mock_init_cloudinary.return_value = None
        mock_cloudinary_image.return_value.build_url.return_value = "https://example.com/image.jpg"
        mock_cloudinary_uploader_upload.return_value.get.return_value = "test_public_id"

        # Mocking the database objects
        mock_tag = Tag(id=1, title="Tag 1", created_at="2023-11-01T12:00:00")
        mock_db_photo = MagicMock()
        mock_db_photo = Photo(
            id=1,
            image_url="https://example.com/image.jpg",
            qr_transform="https://example.com/qr_transform.jpg",
            likes=10,
            description="Photo description",
            created_at="2023-11-01T12:00:00",
            updated_at="2023-11-01T12:00:00",
        )
        mock_db_photo.tags = [mock_tag]

        photo_resp = PhotoResponse(
            id=1,
            image_url="https://example.com/image.jpg",
            qr_transform="https://example.com/qr_transform.jpg",
            likes=10,
            description="Photo description",
            created_at="2023-11-01T12:00:00",
            updated_at="2023-11-01T12:00:00",
            tags=[Tag(id=1, title="Tag 1", created_at="2023-11-01T12:00:00")]
        )

        mock_db_session.query().filter().first.return_value = None
        mock_db_session.commit.return_value = None
        mock_db_session.refresh.return_value = None
        mock_db_session.query().filter().first.return_value = mock_tag

        # Mocking the PhotoResponse object
        expected_photo_response_data = {
            "id": 1,
            "image_url": "https://example.com/image.jpg",
            # ... populate other necessary fields here
            "tags": [TagResponse(id=1, title="Tag 1", created_at="2023-11-01T12:00:00")]
        }

        with patch('src.repository.photos.datetime') as mock_datetime:
            mock_datetime.now.return_value.timestamp.return_value = mock_timestamp

            # Call the function to be tested
            result = await create_user_photo(mock_photo_create, mock_upload_file, mock_current_user, mock_db_session)

        # Assertions
        self.assertIsInstance(result, photo_resp)
        # Add more assertions based on your expected behavior and the result obtained
        # Make assertions to check if the expected_photo_response_data matches the result obtained
        self.assertEqual(result.id, expected_photo_response_data['id'])
        self.assertEqual(result.image_url, expected_photo_response_data['image_url'])
        # ... add assertions for other fields as well

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
        self.assertEqual(result.description, "Photo updated description")
        self.assertEqual(result.tags, ["Updated tag"])

    @patch('src.repository.photos.get_public_id_from_image_url')
    @patch('src.repository.photos.init_cloudinary')
    async def test_delete_user_photo(self, mock_init_cloudinary, mock_get_public_id_from_image_url):
        # Mock data
        photo_id = 1
        user_id = 1
        is_admin = False
        db_session = MagicMock()

        mock_photo = MagicMock()
        mock_photo.user_id = user_id

        mock_db_query = MagicMock()
        mock_db_query.filter().first.return_value = mock_photo
        db_session.query.return_value = mock_db_query

        mock_get_public_id_from_image_url.return_value = "test_public_id"

        async def async_destroy(*args, **kwargs):
            pass

        mock_destroy = AsyncMock(side_effect=async_destroy)

        with patch('src.repository.photos.destroy', mock_destroy):
            result = await delete_user_photo(photo_id, user_id, is_admin, db_session)

        mock_db_query.filter.assert_called_once_with(Photo.id == photo_id)
        mock_destroy.assert_called_once_with("PhotoshareApp_qrcode/test_public_id_qr")
        db_session.delete.assert_called_once_with(mock_photo)
        db_session.commit.assert_called_once()

        self.assertEqual(result, mock_photo)

    async def test_delete_user_photo_not_found(self):
        photo = Photo()
        self.session.query().filter().first.return_value = None
        result = await delete_user_photo(photo_id=1, user_id=1, is_admin=True, db=self.session)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
