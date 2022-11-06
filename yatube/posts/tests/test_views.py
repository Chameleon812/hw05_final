import shutil
import tempfile
from datetime import date
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, Comment, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewTests(TestCase):
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
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Текст тестового поста',
            author=cls.user_creator,
            group=cls.group,
            pub_date=date.today(),
            image=tst_img
        )
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user_creator,
            text="Текст тестового комментария к посту",
        )
        cls.posts = cls.post.author.posts.select_related('author')
        cls.cnt_posts = cls.post.author.posts.count()
        cls.endpoints = {
            'index': 'posts:index',
            'group_list': 'posts:group_list',
            'profile': 'posts:profile',
            'post_detail': 'posts:post_detail',
            'post_create': 'posts:post_create',
            'post_edit': 'posts:post_edit'}

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.post_creator = Client()
        self.post_creator.force_login(self.user_creator)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_uncreator)
        cache.clear()

    def checking_correct_post(self, post):
        self.assertEqual(self.post.author, post.author)
        self.assertEqual(self.post.text, post.text)
        self.assertEqual(self.post.group, post.group)
        self.assertEqual(self.post.pub_date, post.pub_date)
        self.assertEqual(self.post.image, post.image)

    def checking_correct_group(self, group):
        self.assertEqual(self.group.title, group.title)
        self.assertEqual(self.group.slug, group.slug)
        self.assertEqual(self.group.description, group.description)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse(
                self.endpoints['index']
            ): 'posts/index.html',
            reverse(
                self.endpoints['group_list'], kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                self.endpoints['profile'],
                kwargs={'username': self.post.author}
            ): 'posts/profile.html',
            reverse(
                self.endpoints['post_detail'], kwargs={'post_id': self.post.pk}
            ): 'posts/post_detail.html',
            reverse(
                self.endpoints['post_create']
            ): 'posts/create_post.html',
            reverse(
                self.endpoints['post_edit'], kwargs={'post_id': self.post.pk}
            ): 'posts/create_post.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.post_creator.get(reverse_name)

                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Проверка контекста главной страницы."""
        response = self.authorized_client.get(reverse(self.endpoints['index']))

        self.checking_correct_post(response.context['page_obj'][0])

    def test_grouplist_show_correct_context(self):
        """Проверка контекста страницы группы."""
        response = self.authorized_client.get(reverse(
            self.endpoints['group_list'], kwargs={'slug': self.group.slug}
        ))

        self.checking_correct_group(response.context.get('group'))
        self.checking_correct_post(response.context['page_obj'][0])

    def test_profile_show_correct_context(self):
        """Проверка контекста профиля автора."""
        response = self.authorized_client.get(reverse(
            self.endpoints['profile'], kwargs={'username': self.post.author}
        ))

        page_cntx = response.context['page_obj'][0]
        cnt_cntx = response.context.get('count_posts')
        author_cntx = response.context.get('author')

        self.checking_correct_post(page_cntx)
        self.assertEqual(cnt_cntx, self.cnt_posts)
        self.assertEqual(author_cntx, self.post.author)

    def test_postdetail_show_correct_context(self):
        """Проверка контекста страницы поста."""
        response = self.authorized_client.get(reverse(
            self.endpoints['post_detail'], kwargs={'post_id': self.post.pk}
        ))
        text_cntx = response.context.get('post')
        cnt_cntx = response.context.get('post_count')

        self.checking_correct_post(text_cntx)
        self.assertEqual(cnt_cntx, self.cnt_posts)

    def test_editpost_show_correct_context(self):
        """Проверка контекста страницы редактирования поста."""
        response = self.post_creator.get(reverse(
            self.endpoints['post_edit'], kwargs={'post_id': self.post.pk}
        ))
        is_edit = response.context['is_edit']

        self.assertTrue(is_edit)
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_addpost_show_correct_context(self):
        """Проверка контекста страницы создания поста."""
        response = self.authorized_client.get(reverse(
            self.endpoints['post_create']
        ))

        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_correctly_added_post(self):
        """Проверка на корректное добавление поста."""
        response_index = self.authorized_client.get(reverse(
            self.endpoints['index']
        ))
        response_group = self.authorized_client.get(reverse(
            self.endpoints['group_list'], kwargs={'slug': f'{self.group.slug}'}
        ))
        response_profile = self.authorized_client.get(reverse(
            self.endpoints['profile'],
            kwargs={'username': f'{self.post.author}'}
        ))
        index = response_index.context['page_obj']
        group = response_group.context['page_obj']
        profile = response_profile.context['page_obj']

        self.assertIn(self.post, index, 'На главную пост не добавился')
        self.assertIn(self.post, group, 'В группу пост не добавился')
        self.assertIn(self.post, profile, 'В профиль пост не добавился')

    def test_cache_index(self):
        """Проверка кэширования главной страницы"""
        post_cnt = Post.objects.count()
        response = self.authorized_client.get(reverse(self.endpoints['index']))
        content_before = response.content
        Post.objects.get().delete()
        self.assertEqual(Post.objects.count(), post_cnt - 1)
        content_after = response.content
        self.assertEqual(content_before, content_after)
        after_clear = self.authorized_client.get(reverse(
            self.endpoints['index']
        ))
        self.assertNotEqual(content_before, after_clear)


class PaginatorViewsTest(TestCase):
    COUNT_TEST_POSTS: int = 15

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_auth = User.objects.create(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Текст описания тестовой группы'
        )
        cls.some_posts = [
            Post(
                author=cls.user_auth,
                text=f'Тестовый пост{post_num}',
                group=cls.group
            )
            for post_num in range(cls.COUNT_TEST_POSTS)
        ]
        Post.objects.bulk_create(cls.some_posts)

    def setUp(self):
        self.not_authorized = Client()
        self.authorized = Client()
        self.authorized.force_login(self.user_auth)

    def test_correct_page_context_guest_client(self):
        """Проверка количества постов на первой и второй страницах."""
        pages: tuple = (reverse('posts:index'),
                        reverse('posts:profile',
                                kwargs={
                                    'username': f'{self.user_auth.username}'
                                }),
                        reverse('posts:group_list',
                                kwargs={
                                    'slug': f'{self.group.slug}'
                                }))

        for page in pages:
            response_1page = self.not_authorized.get(page)
            response_2page = self.not_authorized.get(page + '?page=2')
            page1_cnt = len(response_1page.context['page_obj'])
            page2_cnt = len(response_2page.context['page_obj'])

            self.assertEqual(page1_cnt, settings.POSTS_PER_PAGE)
            self.assertEqual(
                page2_cnt,
                self.COUNT_TEST_POSTS - settings.POSTS_PER_PAGE
            )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower = User.objects.create(
            username='follower_man')
        cls.following = User.objects.create(
            username='following_man')
        cls.follower_post = Post.objects.create(
            text='Текст тестового поста follower',
            author=cls.follower,
        )
        cls.following_post = Post.objects.create(
            text='Текст тестового поста following',
            author=cls.following,
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_follower = Client()
        self.authorized_follower.force_login(self.follower)
        self.authorized_following = Client()
        self.authorized_following.force_login(self.following)

    def test_authorized_user_can_follow(self):
        """Авторизованный пользователь может подписываться."""
        follow_count = Follow.objects.count()
        response_follow = self.authorized_follower.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.following}
        ))
        self.assertRedirects(
            response_follow,
            reverse('posts:profile',
                    kwargs={'username': self.following}
                    )
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=self.follower,
                author=self.following
            ).exists()
        )

    def test_authorized_user_can_unfollow(self):
        """Авторизованный пользователь может отписываться."""
        Follow.objects.create(user=self.follower, author=self.following)
        follow_count = Follow.objects.count()
        response_unfollow = self.authorized_follower.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.following}
        ))
        self.assertRedirects(
            response_unfollow,
            reverse('posts:profile',
                    kwargs={'username': self.following}
                    )
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertFalse(
            Follow.objects.filter(
                user=self.follower,
                author=self.following
            ).exists()
        )

    def test_follower_get_follow_index(self):
        """Новая запись пользователя появляется в ленте у подписчика."""
        Follow.objects.create(user=self.follower, author=self.following)
        response_follower = self.authorized_follower.get(
            reverse('posts:follow_index'))
        first_post = response_follower.context['page_obj'][0]
        self.assertEqual(first_post.text, self.following_post.text)
        self.assertEqual(first_post.author, self.following)

    def test_unfollower_dont_get_follow_index(self):
        """Новая запись пользователя не появляется в ленте у не подписчиков"""
        response_following = self.authorized_following.get(reverse(
            'posts:follow_index'))
        self.assertEqual(
            response_following.context['page_obj'].paginator.count, 0)
