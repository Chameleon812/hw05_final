# Generated by Django 2.2.16 on 2022-11-02 17:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Введите название группы', max_length=200, verbose_name='Название группы')),
                ('slug', models.SlugField(help_text='Укажите уникальный адрес для страницы группы.Используйте только латиницу, цифры,дефисы и знаки подчёркивания', unique=True, verbose_name='URL')),
                ('description', models.TextField(help_text='Введите описание группы', verbose_name='описание')),
            ],
            options={
                'verbose_name': 'группа',
                'verbose_name_plural': 'группы',
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(help_text='Напишите текст поста', verbose_name='Текст записи')),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='дата публикации')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to=settings.AUTH_USER_MODEL, verbose_name='автор')),
                ('group', models.ForeignKey(blank=True, help_text='Группа, к которой будет относиться пост', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='posts', to='posts.Group', verbose_name='группа')),
            ],
            options={
                'verbose_name': 'пост',
                'verbose_name_plural': 'посты',
                'ordering': ('-pub_date',),
            },
        ),
    ]
