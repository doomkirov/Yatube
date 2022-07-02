import shutil
import tempfile

from posts.models import Post, Group, Comment

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='TitleTest',
            slug='test_slug',
            description='Тестовый description'
        )
        cls.small_jpg = (            
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.jpg',
            content=cls.small_jpg,
            content_type='image/jpg'
        )
        cls.another_img = SimpleUploadedFile(
            name='another.jpg',
            content=cls.small_jpg,
            content_type='image/jpg'
        )
        cls.post = Post.objects.create(
            text='Заранее создано',
            group=cls.group,
            author=cls.author,
            image=cls.another_img
        )
        cls.comment = Comment.objects.create(
            text='Any text',
            author=cls.author,
            post=cls.post
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.author)
        self.unauthorized_client = Client()

    def test_post_create(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': self.uploaded
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.author.username}
        ))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        created_post_data = {
            'text': 'Тестовый текст',
            'group': self.group,
            'image': 'posts/small.jpg',
            'author': self.author,
        }
        for field_name, expected_value in created_post_data.items():
            with self.subTest(expected_value=expected_value):
                field = getattr(Post.objects.latest('pub_date'), field_name)
                self.assertEquals(
                    field,
                    expected_value
                )

    def test_post_edit(self):
        form_data = {
            'text': 'Проверка редактирования',
            'group': self.group.id,
            'image': 'None'
        }
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}
        ))
        self.assertEqual(Post.objects.count(), 1)
        edited_post_data = {
            'text': 'Проверка редактирования',
            'group': self.group,
            'image': self.post.image,
            'author': self.author
        }
        for field_name, expected_value in edited_post_data.items():
            with self.subTest(expected_value=expected_value):
                field = getattr(Post.objects.latest('pub_date'), field_name)
                self.assertEquals(
                    field,
                    expected_value
                )

    def test_post_detail_comment_created(self):
        form_data = {
            'post': self.post,
            'text': 'Комментарий'
        }
        response = self.author_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}
        ))
        self.assertEqual(
            getattr(Comment.objects.latest('created'), 'text'),
            'Комментарий'
        )

    def test_unauthorized_comment(self):
        form_data = {
            'post': self.post,
            'text': 'Комментарий без авторизации'
        }
        response = self.unauthorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(
            Comment.objects.latest('created').text,
            'Комментарий без авторизации'
        )
