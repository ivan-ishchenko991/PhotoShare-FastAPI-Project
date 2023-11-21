import unittest
from unittest.mock import MagicMock,patch 
from datetime import datetime

from sqlalchemy.orm import Session
from src.database.models import User, Photo
from src.repository.qr_code import make_qr_code_for_photo

class TestQRCode(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db_session = MagicMock(spec=Session)
        self.user = User(id=1)

    @patch("src.repository.qr_code.cloudinary.uploader.upload")
    @patch("src.repository.qr_code.qrcode.QRCode")
    async def test_make_qr_code_for_photo(self, mock_qrcode, mock_cloudinary):

        photo = Photo(id=1,
                      image_url="example_url",
                      description="Test description",
                      created_at=datetime.now(),
                      updated_at=datetime.now(),
                      likes=1,
                      who_liked="example@gmail.com",
                      user_id=self.user.id,
                      image_transform="image_transform_example",
                      qr_transform=None,
                      public_id="public_example_url")


        self.db_session.query().filter().first.return_value = photo

        mock_cloudinary.return_value.build_url.return_value = "https://www.example.com/example_image.png"

        result = await make_qr_code_for_photo(photo.id, self.user, self.db_session)

        self.assertIsNotNone(result.qr_transform)
        mock_qrcode.return_value.add_data.assert_called_once_with(photo.image_url)
        mock_qrcode.return_value.make.assert_called_once_with(fit=True)
        mock_qrcode.return_value.make_image.assert_called_once_with(fill_color="black", back_color="white")
        mock_cloudinary.assert_called_once()
        self.db_session.commit.assert_called_once()

if __name__ == "__main__":
    unittest.main()