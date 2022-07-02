# posts/tests/test_urls.py
from urllib import response
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from posts.models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.second_author = User.objects.create_user(username='second_author')
        cls.group = Group.objects.create(
            title='TitleTest',
            slug='test',
            description='Тестовый description'
        )
        cls.post = Post.objects.create(
            text='Textpost',
            author=cls.author,
            group=cls.group,
        )
        cls.second_post = Post.objects.create(
            text='SecondTestPost',
            author=cls.second_author,
            group=cls.group,
        )
        cls.templates_url_names = {
            '': 'posts/index.html',
            '/group/test/': 'posts/group_list.html',
            '/profile/test_user/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.second_author)
        self.test_post_author = Client()
        self.test_post_author.force_login(self.author)

    def test_guest_client(self):
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
        self.assertRedirects(
            self.guest_client.get('/create/'),
            '/auth/login/?next=/create/',
        )
        self.assertRedirects(
            self.guest_client.get('/posts/1/edit/'),
            '/auth/login/?next=/posts/1/edit/'
        )

    def test_authorized_client(self):
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            self.authorized_client.get('/create/'),
            'posts/create_post.html'
        )
        self.assertRedirects(
            self.authorized_client.get('/posts/1/edit/'),
            '/'
        )

    def test_post_author_tests(self):
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.test_post_author.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            self.test_post_author.get('/create/'),
            'posts/create_post.html'
        )
        self.assertTemplateUsed(
            self.test_post_author.get('/posts/1/edit/'),
            'posts/create_post.html'
        )

    def test_post_author_cant_edit_other_post(self):
        self.assertRedirects(
            self.test_post_author.get('/posts/2/edit/'),
            '/'
        )

    def test_unexisting_page(self):
        response = self.test_post_author.get('/unexisting_page/')
        self.assertEqual(
            response.status_code,
            404
        )
        self.assertTemplateUsed(
            response,
            'core/404.html'
        )
