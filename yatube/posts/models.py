from core.models import CreatedModel
from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        'Group name',
        max_length=200,
        help_text='Enter a group name'
    )
    slug = models.SlugField(
        verbose_name='URL', unique=True,
        help_text=(
            'Specify a unique address for the group page.'
            'Use only Latin, numbers,'
            'hyphens and underscores.'
        )
    )
    description = models.TextField(
        verbose_name='description',
        help_text='Enter a description for the group'
    )

    class Meta:
        verbose_name = 'group'
        verbose_name_plural = 'groups'

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField('entry text', help_text='Write the text of the post')
    pub_date = models.DateTimeField(
        verbose_name='publication date',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        null=False,
        on_delete=models.CASCADE,
        verbose_name='author',
        related_name='posts'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='group',
        related_name='posts',
        help_text='The group to which the post belongs'
    )
    image = models.ImageField(
        'Image',
        upload_to='posts/',
        help_text='Add an image',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'post'
        verbose_name_plural = 'posts'

    def __str__(self):
        return self.text[:15]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='post'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='comment author'
    )
    text = models.TextField(
        'Comment text',
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'comment'
        verbose_name_plural = 'comments'

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='follower'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='futhor'
    )

    class Meta:
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'author'), name='unique_author_user_following'
            ),
        )
