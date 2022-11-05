from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client

from posts.models import Post, Group


User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_creator = User.objects.create(username='user_cr')
        cls.user_uncreator = User.objects.create(username='user_un')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Текст описания тестовой группы'
        )
        cls.post = Post.objects.create(
            text='Текст тестового поста',
            author=cls.user_creator,
            group=cls.group
        )
        cls.endpoints = {
            'group_list': f'/group/{cls.group.slug}/',
            'profile': f'/profile/{cls.post.author}/',
            'post_detail': f'/posts/{cls.post.id}/',
            'edit_post': f'/posts/{cls.post.id}/edit/',
            'create_post': '/create/',
            'index': '/'
        }

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='guest')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_uncreator)
        self.post_creator = Client()
        self.post_creator.force_login(self.user_creator)
        cache.clear()

    def test_pages_for_all(self):
        """Проверка страниц доступных всем."""
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
        """Проверка страниц для автора."""
        response = self.post_creator.get(self.endpoints['edit_post'])

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_for_uncreator(self):
        """Проверка доступа авторизованного пользователя к созданию поста"""
        response = self.authorized_client.get(self.endpoints['create_post'])

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_guest_for_edit_post(self):
        """Проверка на доступ гостя к странице редактирования поста."""
        response = self.guest_client.get(self.endpoints['edit_post'])

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

    def test_uncreator_post_edit(self):
        """Проверка на доступ не автора к странице редактирования поста."""
        response = self.authorized_client.get(self.endpoints['edit_post'])

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, self.endpoints['post_detail'])

    def test_page_not_exist(self):
        """Страницы, которых не предусмотрено."""
        response = self.guest_client.get('/owls/')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_templates_for_urls(self):
        """Корректность шаблонов."""
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

    def test_follow_index_page(self):
        """Страница подписок доступна автору."""
        response = self.post_creator.get('/follow/')

        self.assertEqual(response.status_code, HTTPStatus.OK)
