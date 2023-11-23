import unittest
from unittest.mock import MagicMock, Mock

from fastapi import UploadFile
from sqlalchemy.orm import Session

from src.database.models import Photo, User
from src.schemas import PhotoResponse, PhotoCreate, PhotoUpdate, TagResponse
from src.repository.photos import (
    get_user_photos,
    get_user_photo_by_id,
    update_user_photo,
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

    # async def test_update_user_photo(self):
    #     photo = PhotoResponse(
    #         id=1,
    #         image_url="https://example.com/image.jpg",
    #         qr_transform="https://example.com/qr_transform.jpg",
    #         likes=10,
    #         description="Photo updated description",
    #         created_at="2023-11-01T12:00:00",
    #         updated_at="2023-11-01T12:00:00",
    #         tags=[TagResponse(id=1, title="Tag 1", created_at="2023-11-01T12:00:00")]
    #     )
    #
    #     photo_update = PhotoUpdate(
    #         description="Photo updated description",
    #         tags=["Updated tag"]
    #     )
    #
    #     self.session.query().filter().first.return_value = photo
    #     result = await update_user_photo(
    #         photo=photo,
    #         updated_photo=photo_update,
    #         current_user=self.user,
    #         db=self.session
    #     )
    #     self.assertEqual(result.description, "Photo updated description")
    #     self.assertEqual(result.tags, ["Updated tag"])

    async def test_delete_user_photo_not_found(self):
        photo = Photo()
        self.session.query().filter().first.return_value = None
        result = await delete_user_photo(photo_id=1, user_id=1, is_admin=True, db=self.session)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
