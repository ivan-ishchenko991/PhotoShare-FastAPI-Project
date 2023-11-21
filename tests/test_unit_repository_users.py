import unittest
from unittest.mock import MagicMock
from datetime import datetime

from sqlalchemy.orm import Session
from src.schemas import UserModel
from src.database.models import  User, Photo, Roles
from src.repository.users import (
    get_user_by_email,
    create_user,
    update_avatar,
    update_token,
    confirmed_email,
    block_user,
    change_role,
    put_a_like,
    dislike,
    delete_like_admin_moder,
)
class TestUsers(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=1)

    async def test_get_user_by_email(self):
        user = User(email = "test@gmail.com" )
        self.session.query().filter().first.return_value = user
        result = await get_user_by_email(email="test@gmail.com", db=self.session)
        self.assertEqual(result, user)

    async def test_get_user_by_email_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await get_user_by_email(email="test@gmail.com", db=self.session)
        self.assertIsNone(result)

    async def test_create_user(self):
        user = UserModel(username = "TestExample",email="test@gmail.com",password = "password")
        new_user = User(**user.dict(), avatar="https://www.gravatar.com/avatar/1aedb8d9dc4751e229a335e371db8058")
        self.session.add.return_value = None
        self.session.commit.return_value = None
        self.session.refresh.return_value = None
        result = await create_user(body=user, db=self.session)
        self.assertEqual(result.username, new_user.username)
        self.assertEqual(result.email, new_user.email)
        self.assertEqual(result.avatar, new_user.avatar)

    async def test_update_avatar(self):
        user = User(email="test@example.com", avatar="old_url")
        self.session.query().filter().first.return_value = user
        new_url = "new_url"
        result = await update_avatar(email="test@example.com", url=new_url, db=self.session)
        self.assertEqual(result, user)
        self.assertEqual(result.avatar, new_url)

    async def test_update_token(self):
        user = User(email="test@example.com")
        new_token = "new_token"
        result = await update_token(user=user, token=new_token, db=self.session)
        self.assertEqual(user.refresh_token, new_token)

    async def test_confirmed_email(self):
        user = User(email="test@example.com", confirmed_email=False)
        self.session.query().filter().first.return_value = user
        self.session.commit.return_value = None
        result = await confirmed_email(email="test@example.com", db=self.session)
        self.assertTrue(user.confirmed_email)
        self.assertIsNone(result)
    
    async def test_block_user(self):
        user = User(email = "test@example.com")
        self.session.query().filter().first.return_value = user
        self.session.commit.return_value = None
        result = await block_user(user_email="test@example.com", db=self.session)
        self.assertTrue(user.is_banned)
        self.assertIsNone(result)

    async def test_change_role(self):
        user = User(email = "test@example.com", roles = Roles.moderator)
        self.session.query().filter().first.return_value = user
        result = await change_role("test@example.com", Roles.moderator, self.session) 
        self.assertEqual(result, "OK")
        self.assertEqual(user.roles, Roles.moderator)     

    async def test_change_role_is_admin(self):
        user = User(email = "test@example.com", roles = Roles.admin)             
        self.session.query().filter().first.return_value = user
        result = await change_role("test@example.com", Roles.moderator, self.session)
        self.assertEqual(result, "NOT OK")
        self.assertEqual(user.roles, Roles.admin)
    
    async def test_put_a_like(self):
        user = User(email= "user@example.com")
        photo = Photo(id = 1, likes = 0, who_liked="")
        self.session.query().filter().first.return_value = photo
        result = await put_a_like(photo_id=photo.id, current_user=user, db=self.session)
        self.assertEqual(result, "OK")
        self.assertEqual(photo.likes, 1)
        self.assertIn(user.email, photo.who_liked)

    async def test_put_a_like_user_already_liked(self):
        user = User(email= "user@example.com")
        photo = Photo(id = 1, likes = 1 ,who_liked="user@example.com,")
        self.session.query().filter().first.return_value = photo
        result = await put_a_like(photo_id=photo.id, current_user=user, db=self.session)
        self.assertEqual(result, "NOT OK")
        self.assertEqual(photo.likes, 1)

    async def test_dislike(self):
        user = User(email= "user@example.com")
        photo = Photo(id = 1,likes = 1, who_liked="user@example.com,")
        self.session.query().filter().first.return_value = photo
        result = await dislike(photo_id=photo.id, current_user=user, db=self.session)
        self.assertEqual(result, "OK")
        self.assertEqual(photo.likes, 0)
        self.assertNotIn(user.email, photo.who_liked)

    async def test_dislike_user_already_disliked(self):
        user = User(email= "user@example.com")
        photo = Photo(id = 1, likes = 1, who_liked="")
        self.session.query().filter().first.return_value = photo
        result = await dislike(photo_id=photo.id, current_user=user, db=self.session)
        self.assertEqual(result, "NOT OK")
        self.assertEqual(photo.likes, 1)

    async def test_delete_like_admin_moder_user_not_liked_before(self):
        user = User(email= "user@example.com")
        photo = Photo(id = 1,likes = 1, who_liked="")
        self.session.query().filter().first.return_value = photo
        result = await delete_like_admin_moder(user_email=user.email, photo_id=photo.id, db=self.session)
        self.assertEqual(result, "NOT OK")
        self.assertEqual(photo.likes, 1)

    async def test_delete_like_admin_moder_user_liked_before(self):
        user = User(email= "user@example.com")
        photo = Photo(id = 1,likes = 1, who_liked="user@example.com,")
        self.session.query().filter().first.return_value = photo
        result = await delete_like_admin_moder(user_email=user.email, photo_id=photo.id, db=self.session)
        self.assertEqual(result, "OK")
        self.assertEqual(photo.likes, 0)
        self.assertNotIn(user.email, photo.who_liked)


if __name__ == '__main__':
    unittest.main()
