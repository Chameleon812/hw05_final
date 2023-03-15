from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test post to check',
        )

    def test_post_model_object_name(self):
        """We check that __str__ works correctly for the Post model."""
        post = PostModelTest.post
        object_name = str(post)

        self.assertEqual(object_name, post.text[:15])

    def test_post_model_verbose_name(self):
        """Check for verbose_name."""
        field_verboses = {
            'text': 'entry text',
            'author': 'author',
            'group': 'group',
        }
        post = PostModelTest.post

        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )

    def test_post_model_help_text(self):
        """Checking help_text."""
        field_help_texts = {
            'text': 'Write the text of the post',
            'group': 'The group to which the post belongs',
        }
        post = PostModelTest.post

        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Test group',
            slug='Test slug',
            description='Test description',
        )

    def test_group_model_object_name(self):
        """We check that __str__ works correctly for the Group model."""
        group = GroupModelTest.group
        object_name = group.title

        self.assertEqual(object_name, str(group))
