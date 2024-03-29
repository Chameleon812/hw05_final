import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_creator = User.objects.create(username='user_cr')
        cls.user_uncreator = User.objects.create(username='user_un')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test_slug',
            description='Test group description text'
        )
        test_img = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        tst_img = SimpleUploadedFile(
            name='test_img.gif',
            content=test_img,
            content_type='image/gif')
        cls.post = Post.objects.create(
            text='Test post text',
            author=cls.user_creator,
            group=cls.group,
            image=tst_img
        )

        cls.endpoints = {
            'group_list': f'/group/{cls.group.slug}/',
            'profile': f'/profile/{cls.post.author}/',
            'post_detail': f'/posts/{cls.post.id}/',
            'edit_post': f'/posts/{cls.post.id}/edit/',
            'create_post': '/create/',
            'index': '/'
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='guest')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_uncreator)
        self.post_creator = Client()
        self.post_creator.force_login(self.user_creator)
        settings.MEDIA_ROOT = tempfile.mkdtemp()
        cache.clear()

    def test_pages_for_all(self):
        """Checking the pages available to everyone."""
        pages_for_all = {
            self.endpoints['index']: 'posts/index.html',
            self.endpoints['group_list']: 'posts/group_list.html',
            self.endpoints['profile']: 'posts/profile.html',
            self.endpoints['post_detail']: 'posts/post_detail.html'
        }

        for page, template in pages_for_all.items():
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_pages_for_author(self):
        """Check pages for author."""
        response = self.post_creator.get(self.endpoints['edit_post'])

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_for_uncreator(self):
        """Checking the access of an authorized user to create a post."""
        response = self.authorized_client.get(self.endpoints['create_post'])

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_for_edit_post(self):
        """Checking for guest access to the post editing page."""
        response = self.guest_client.get(self.endpoints['edit_post'])

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

    def test_uncreator_post_edit(self):
        """Checking for non-author access to the post edit page."""
        response = self.authorized_client.get(self.endpoints['edit_post'])

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, self.endpoints['post_detail'])

    def test_page_not_exist(self):
        """Pages not provided."""
        response = self.guest_client.get('/owls/')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_templates_for_urls(self):
        """Template correctness."""
        templates_urls = {
            self.endpoints['index']: 'posts/index.html',
            self.endpoints['group_list']: 'posts/group_list.html',
            self.endpoints['profile']: 'posts/profile.html',
            self.endpoints['post_detail']: 'posts/post_detail.html',
            self.endpoints['edit_post']: 'posts/create_post.html',
            self.endpoints['create_post']: 'posts/create_post.html',
        }

        for url, template in templates_urls.items():
            with self.subTest(url=url):
                response = self.post_creator.get(url)

                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_follow_index_page(self):
        """The subscription page is available to the author."""
        response = self.post_creator.get('/follow/')

        self.assertEqual(response.status_code, HTTPStatus.OK)
