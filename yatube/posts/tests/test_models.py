# deals/tests/tests_models.py
from django.test import TestCase
from django.contrib.auth import get_user_model

from posts.models import Post, Group

User = get_user_model()


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='TitleTest',
            slug='test',
            description='Тестовый description'
        )
        cls.post = Post.objects.create(
            text='Textpost',
            author=cls.author,
            group=cls.group,
            pub_date='22.02.2022'
        )

    def test_str_out(self):
        group = GroupModelTest.group
        post = GroupModelTest.post
        self.assertEqual(group.__str__(), group.title)
        self.assertEqual(post.__str__(), post.text[:15])
