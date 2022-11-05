import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm, CommentForm
from posts.models import Group, Post, Comment

User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormCreateTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.creator = User.objects.create(username="creator")
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Текст описания тестовой группы',
        )
        cls.post = Post.objects.create(
            text='Текст тестового поста',
            author=cls.creator,
            group=cls.group,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.creator_client = Client()
        self.creator_client.force_login(self.creator)
        cache.clear()

    def test_creator_create_new_post(self):
        """Создание нового поста авторизованным пользователем."""
        post_count = Post.objects.count()
        ima1_gif = Post.test_img
        uploaded = SimpleUploadedFile(
            name='test1.gif',
            content=ima1_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст для заполнения формы',
            'group': self.group.id,
            'image': uploaded,
        }

        response = self.creator_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.creator}
        ))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                author=self.creator,
                text=form_data['text'],
                group=form_data['group'],
                image=f'posts/{uploaded.name}',
            ).exists()
        )

    def test_guest_create_new_post(self):
        """Тест на возможность создания поста неавторизованным юзером."""
        post_count = Post.objects.count()
        ima2_gif = Post.test_img
        uploaded = SimpleUploadedFile(
            name='test2.gif',
            content=ima2_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст для заполнения формы',
            'group': self.group.id,
            'image': uploaded,
        }

        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            '/auth/login/?next=%2Fcreate%2F')
        self.assertEqual(Post.objects.count(), post_count)

    def test_creator_edit_post(self):
        """Редактирование поста авторизованным пользователем."""
        post_count = Post.objects.count()
        ima3_gif = Post.test_img
        uploaded = SimpleUploadedFile(
            name='test3.gif',
            content=ima3_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст для заполнения формы',
            'group': self.group.id,
            'image': uploaded,
        }

        response = self.creator_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk},))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data["group"],
                image=f'posts/{uploaded.name}'
            ).exists()
        )

    def test_guest_edit_post(self):
        """Тест на возможность редактирования поста неавторизованным юзером."""
        post_count = Post.objects.count()
        ima4_gif = Post.test_img
        uploaded = SimpleUploadedFile(
            name='test4.gif',
            content=ima4_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст для заполнения формы',
            'group': self.group.id,
            'image': uploaded,
        }

        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            '/auth/login/?next=%2Fposts%2F1%2Fedit%2F')
        self.assertEqual(Post.objects.count(), post_count)


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()
        cache.clear()

    def test_text_label(self):
        text_label = PostFormTests.form.fields['text'].label

        self.assertEqual(text_label, 'Текст записи')

    def test_group_label(self):
        group_label = PostFormTests.form.fields['group'].label

        self.assertEqual(group_label, 'Сообщество')

    def test_image_label(self):
        image_label = PostFormTests.form.fields['image'].label

        self.assertEqual(image_label, 'Картинка')


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='commentator')
        cls.post = Post.objects.create(
            text='Текст тестового поста',
            author=cls.user
        )
        cls.form = CommentForm()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_user_create_comment(self):
        """User создает коммент к посту."""
        comment_cnt = Comment.objects.count()
        form_data = {
            'text': 'Текст комментатора',
            'author': self.user,
            'post': self.post.id
        }

        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': CommentFormTests.post.id}
                    ),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': CommentFormTests.post.id}
        ))
        self.assertEqual(Comment.objects.count(), comment_cnt + 1)
        self.assertTrue(Comment.objects.filter(
            text='Текст комментатора',
            author=self.user,
            post=self.post.id
        ))

    def test_guest_create_comment(self):
        """Guest создает коммент к посту."""
        comment_cnt = Comment.objects.count()
        form_data = {
            'text': 'Текст комментатора',
        }

        response = self.guest_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': CommentFormTests.post.id}
                    ),
            data=form_data,
            follow=True
        )

        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/comment/'
        )
        self.assertEqual(Comment.objects.count(), comment_cnt)
