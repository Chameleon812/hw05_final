from core.models import CreatedModel
from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        'Название группы',
        max_length=200,
        help_text='Введите название группы'
    )
    slug = models.SlugField(
        verbose_name='URL', unique=True,
        help_text=(
            'Укажите уникальный адрес для страницы группы.'
            'Используйте только латиницу, цифры,'
            'дефисы и знаки подчёркивания'
        )
    )
    description = models.TextField(
        verbose_name='описание',
        help_text='Введите описание группы'
    )

    class Meta:
        verbose_name = 'группа'
        verbose_name_plural = 'группы'

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField('Текст записи', help_text='Напишите текст поста')
    pub_date = models.DateTimeField(
        verbose_name='дата публикации',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        null=False,
        on_delete=models.CASCADE,
        verbose_name='автор',
        related_name='posts'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='группа',
        related_name='posts',
        help_text='Группа, к которой будет относиться пост'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        help_text='Добавьте изображение',
        blank=True
    )
    test_img = (
        b"\x47\x49\x46\x38\x39\x61\x02\x00"
        b"\x01\x00\x80\x00\x00\x00\x00\x00"
        b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
        b"\x00\x00\x00\x2C\x00\x00\x00\x00"
        b"\x02\x00\x01\x00\x00\x02\x02\x0C"
        b"\x0A\x00\x3B"
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'пост'
        verbose_name_plural = 'посты'

    def __str__(self):
        return self.text[:15]


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария'
    )
    text = models.TextField(
        'Текст комментария',
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'], name='unique_author_user_following'
            )
        ]
