import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms


import time

from posts.models import Post, Group, Follow
from posts.views import POSTS_ON_VIEW  # не понятно в какой
# settings перенести эту переменную, если в yatube/settings.py,
# то этот файл не импортируется с помощью django.conf.settings,
# это же находится в venv

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.default_author = User.objects.create_user(username='default_auth')
        cls.group = Group.objects.create(
            title='TitleTest',
            slug='test_slug',
            description='Тестовый description'
        )
        cls.not_for_u = Group.objects.create(
            title='GroupNotForU',
            slug='empty',
            description='Test description'
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
        posts = [
            Post(
                text='Textpost',
                author=cls.default_author,
                group=cls.not_for_u,
            )
        ]
        for i in range(1, 13):
            Post.objects.bulk_create(posts)
            time.sleep(0.001)  # из-за того,что записи создаются одновременно,
            # я не могу получить в тестах последнюю запись,
            # ибо она всегда разная,
            # как решить эту проблему без sleep не представляю,
            # если создавать записи без bulk_create, то такой проблемы нет
        cls.post = Post.objects.create(
            text='Post with author and group',
            author=cls.author,
            group=cls.group,
            image=cls.uploaded
        )
        cls.templates_pages_names = {
            'posts/group_list.html': (
                reverse('posts:group_posts', kwargs={'slug': cls.group.slug})
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': cls.author})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': cls.post.pk})
            ),
            'posts/index.html': reverse('posts:index')
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='hasnoname')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.test_post_author = Client()
        self.test_post_author.force_login(self.author)

    def test_guest_client_templates(self):
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertTemplateUsed(
                    self.guest_client.get(reverse_name, follow=True),
                    template
                )
                self.assertEqual(
                    self.guest_client.get(
                        reverse_name,
                        follow=True
                    ).status_code,
                    200
                )
        self.assertTemplateNotUsed(
            self.guest_client.get(reverse('posts:post_create'), follow=True),
            'posts/create_post.html'
        )

    def test_authorized_client_templates(self):
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertTemplateUsed(
                    self.authorized_client.get(reverse_name, follow=True),
                    template
                )
        self.assertTemplateNotUsed(
            self.authorized_client.get(
                reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
                follow=True
            ),
            'posts/create_post.html'
        )

    def test_post_author_template(self):
        self.assertTemplateUsed(
            self.test_post_author.get(
                reverse('posts:post_create'),
                follow=True
            ),
            'posts/create_post.html'
        )

    def test_first_page_contains_records(self):
        self.assertEqual(
            len(self.client.get(reverse('posts:index')).context['page_obj']),
            POSTS_ON_VIEW
        )

    def test_second_page_contains_three_records(self):
        self.assertEqual(
            len(self.client.get(
                reverse('posts:index') + '?page=2'
            ).context['page_obj']),
            3
        )

    def test_context(self):
        self.assertEqual(
            self.test_post_author.get(
                reverse('posts:index')
            ).context['page_obj'][0],
            self.post
        )
        self.assertEqual(
            self.test_post_author.get(
                reverse('posts:group_posts', kwargs={'slug': self.group.slug})
            ).context['page_obj'][0],
            self.post
        )
        self.assertEqual(
            self.test_post_author.get(
                reverse('posts:group_posts', kwargs={'slug': self.group.slug})
            ).context['group'],
            self.group
        )
        self.assertEqual(
            self.test_post_author.get(
                reverse(
                    'posts:profile',
                    kwargs={'username': self.author.username}
                )
            ).context['page_obj'][0],
            self.post
        )
        self.assertEqual(
            self.test_post_author.get(
                reverse(
                    'posts:profile',
                    kwargs={'username': self.author.username}
                )
            ).context['author'],
            self.author
        )
        self.assertEqual(
            self.test_post_author.get(
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': self.post.pk}
                )
            ).context['post'],
            self.post
        )

    def test_image_in_context(self):
        self.assertEqual(
            getattr(self.test_post_author.get(
                reverse('posts:index')
            ).context['page_obj'][0], 'image'),
            'posts/small.jpg'
        )
        self.assertEqual(
            getattr(self.test_post_author.get(
                reverse('posts:group_posts', kwargs={'slug': self.group.slug})
            ).context['page_obj'][0], 'image'),
            'posts/small.jpg'
        )
        self.assertEqual(
            getattr(self.test_post_author.get(
                reverse(
                    'posts:profile',
                    kwargs={'username': self.author.username}
                )
            ).context['page_obj'][0], 'image'),
            'posts/small.jpg'
        )
        self.assertEqual(
            getattr(self.test_post_author.get(
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': self.post.pk}
                )
            ).context['post'], 'image'),
            'posts/small.jpg'
        )

    def test_post_in_pages(self):
        object_in_group = self.test_post_author.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug})
        ).context['page_obj'][0]
        object_in_index = self.test_post_author.get(
            reverse('posts:index')
        ).context['page_obj'][0]
        object_in_profile = self.test_post_author.get(
            reverse('posts:profile', kwargs={'username': self.author.username})
        ).context['page_obj'][0]

        self.assertEqual(object_in_group, self.post)
        self.assertNotEqual(
            object_in_group,
            self.test_post_author.get(
                reverse(
                    'posts:group_posts',
                    kwargs={'slug': self.not_for_u.slug}
                )
            ).context['page_obj'][0]
        )
        self.assertEqual(object_in_index, self.post)
        self.assertEqual(object_in_profile, self.post)
        self.assertNotEqual(
            object_in_profile,
            self.test_post_author.get(
                reverse(
                    'posts:profile',
                    kwargs={'username': self.default_author.username}
                )
            ).context['page_obj'][0]
        )

    def test_post_create_show_correct_context(self):
        response = self.test_post_author.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.models.ModelChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        response = self.test_post_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'group': forms.models.ModelChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(response.context.get('post'), self.post)

    def test_index_cache(self):
        post = Post.objects.create(
            text='Any text',
            author=self.author
        )
        self.assertEqual(
            post,
            self.test_post_author.get(
                reverse('posts:index')
            ).context['page_obj'][0]
        )
        content_with_post = self.test_post_author.get(
            reverse('posts:index')
        ).content
        post.delete()
        self.assertEqual(
            content_with_post,
            self.test_post_author.get(
                reverse('posts:index')
            ).content
        )
        cache.clear()
        self.assertNotEqual(
            content_with_post,
            self.test_post_author.get(
                reverse('posts:index')
            ).content
        )

    def test_authenticated_user_can_follow_and_unfollow(self):
        self.assertRedirects(
            self.authorized_client.get(
                reverse(
                    'posts:profile_follow',
                    kwargs={'username': self.author.username}
                )
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=self.author
            ).exists()
        )
        self.assertRedirects(
            self.authorized_client.get(
                reverse(
                    'posts:profile_unfollow',
                    kwargs={'username': self.author.username}
                )
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.author.username}
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.author
            ).exists()
        )

    def test_new_post_appears_in_follow_index(self):
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.author
            ).exists()
        )
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username}
            )
        )
        self.assertEqual(
            self.authorized_client.get(
                reverse('posts:follow_index')
            ).context['page_obj'][0],
            self.post
        )
        self.assertNotEqual(
            self.authorized_client.get(
                reverse('posts:follow_index')
            ).content,
            self.test_post_author.get(
                reverse('posts:follow_index')
            ).content
        )
