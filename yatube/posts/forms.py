from django.forms import ModelForm

from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': 'Enter post text',
            'group': 'Select the group to which the post belongs',
            'image': 'Choose a picture'
        }
        labels = {
            'text': 'Entry text',
            'group': 'Group',
            'image': 'Picture'
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Comment text'}
