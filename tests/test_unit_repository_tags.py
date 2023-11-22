import unittest
from unittest.mock import MagicMock 
from datetime import datetime

from sqlalchemy.orm import Session
from src.schemas import TagBase
from src.database.models import User, Tag
from src.repository.tags import (
    create_tag,
    get_my_tags,
    get_all_tags,
    get_tag_by_id,
    update_tag,
    remove_tag,
)
class TestUsers(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.session = MagicMock(spec=Session)
        self.user = User(id=1)

    async def test_create_tag(self):
        tag = TagBase(title="example")
        self.session.query().filter().first.return_value = None
        result = await create_tag(body = tag,db=self.session,user=self.user)
        self.assertIsInstance(result, Tag)
        self.assertEqual(result.title, tag.title)
        self.assertEqual(result.user_id, self.user.id)
    
    async def test_tag_already_created(self):
        tag = TagBase(title="example")
        tag_already_created = Tag(title="example",user_id=self.user.id)
        self.session.query().filter().first.return_value = tag_already_created
        result = await create_tag(body = tag,db=self.session,user=self.user)
        self.assertIsNone(result)
        self.session.add.assert_not_called()
        self.session.commit.assert_not_called()
        self.session.refresh.assert_not_called()

    async def test_get_my_tags(self):
        tags = [Tag(),Tag(),Tag()]
        self.session.query().filter().offset().limit().all.return_value = tags
        result = await get_my_tags(skip=0,limit=10,db=self.session,user=self.user)
        self.assertEqual(result,tags)

    async def test_get_all_tags(self):
        tags = [Tag(),Tag(),Tag()]
        self.session.query().offset().limit().all.return_value = tags
        result = await get_all_tags(skip=0,limit=10,db=self.session)
        self.assertEqual(result,tags)

    async def test_get_tag_by_id(self):
        tag = Tag(id=1)
        self.session.query().filter().first.return_value = tag
        result = await get_tag_by_id(tag_id = 1,db=self.session)
        self.assertEqual(result, tag)

    async def test_update_tag(self):
        body = TagBase(title = "example")
        tag = Tag(id = 1, title = body.title)
        self.session.query().filter().first.return_value = tag
        result = await update_tag(tag_id = 1,body=body,db=self.session)
        self.assertEqual(result, tag)
        self.assertEqual(tag.title, body.title)
        self.session.commit.assert_called_once_with()

    async def test_update_tag_not_found(self):
        body = TagBase(title = "example")
        self.session.query().filter().first.return_value = None
        result = await update_tag(tag_id = 1,body=body,db=self.session)
        self.assertIsNone(result)
        self.session.commit.assert_not_called()

    async def test_remove_tag(self):
        tag = Tag(id=1)
        self.session.query().filter().first.return_value = tag
        result = await remove_tag(tag_id = 1,db=self.session)
        self.assertEqual(result,tag)
        self.session.delete.assert_called_once_with(tag)
        self.session.commit.assert_called_once_with()

    async def test_remove_tag_not_found(self):
        self.session.query().filter().first.return_value = None
        result = await remove_tag(tag_id = 1,db=self.session)
        self.assertIsNone(result)
        self.session.delete.assert_not_called()
        self.session.commit.assert_not_called()

if __name__ == '__main__':
    unittest.main()