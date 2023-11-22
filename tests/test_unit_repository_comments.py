import unittest
from unittest.mock import MagicMock 
from datetime import datetime

from sqlalchemy.orm import Session
from src.schemas import CommentBase
from src.database.models import User, Comment
from src.repository.comments import (
    create_comment,
    get_comments_by_photo_id,
    get_comment_by_id,
    update_comment,
    delete_comment,
)
class TestUsers(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=1)

    async def test_create_comment(self):
        comment_base = CommentBase(text = "example")
        comment_db = Comment(text=comment_base.text)
        self.session.query().filter().first.return_value = comment_db
        result = await create_comment(comment = comment_base,photo_id=1,current_user=self.user,db=self.session)
        self.assertIsInstance(result,Comment)
        self.session.add.assert_called_once_with(result)
        self.session.commit.assert_called_once_with()
        self.session.refresh.assert_called_once_with(result)

    async def test_get_comments_by_photo_id(self):
        comment = Comment(photo_id=1)
        self.session.query().filter().all.return_value = comment
        result = await get_comments_by_photo_id(photo_id=1,db=self.session) 
        self.assertEqual(result,comment)

    async def test_get_comments_by_photo_not_found(self):
        self.session.query().filter().all.return_value = None
        result = await get_comments_by_photo_id(photo_id=1,db=self.session)
        self.assertIsNone(result)

    async def test_get_comment_by_id(self):
        comment = Comment()
        self.session.query().filter().first.return_value = comment
        result = await get_comment_by_id(comment_id=1,db=self.session)
        self.assertEqual(result,comment)

    async def test_get_comment_by_id_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await get_comment_by_id(comment_id=1,db=self.session)
        self.assertIsNone(result)

    async def test_update_comment(self):
        comment_base = CommentBase(text="example")
        comment_db = Comment()
        self.session.query().filter().first.return_value = comment_db
        result = await update_comment(comment_id=1,comment=comment_base, db=self.session)
        self.assertEqual(result,comment_db)
        self.session.commit.assert_called_once_with()
        self.session.refresh.assert_called_once_with(comment_db)
    
    async def test_update_comment_not_found(self):
        comment_base = CommentBase(text="example")
        self.session.query().filter().first.return_value = None
        result = await update_comment(comment_id=1,comment=comment_base, db=self.session)
        self.assertIsNone(result)
        self.session.commit.assert_not_called()
        self.session.refresh.assert_not_called()

    async def test_delete_comment(self):
        comment = Comment()
        self.session.query().filter().first.return_value = comment
        result = await delete_comment(comment_id=1,db=self.session)
        self.assertEqual(result,comment)
        self.session.delete.assert_called_once_with(comment)
        self.session.commit.assert_called_once_with()

    async def test_delete_comment_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await delete_comment(comment_id=1,db=self.session)
        self.assertIsNone(result)
        self.session.delete.assert_not_called()
        self.session.commit.assert_not_called()


if __name__ == '__main__':
    unittest.main()