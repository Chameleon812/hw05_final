from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from posts.models import Follow, Post, Group, User
from posts.forms import PostForm, CommentForm
from .utils import paginate_page


@cache_page(20, key_prefix="index_page")
def index(request):
    posts_list = Post.objects.select_related('author')
    page_obj = paginate_page(request, posts_list)
    context = {'page_obj': page_obj, }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.posts.select_related('group')
    page_obj = paginate_page(request, posts_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts_list = author.posts.select_related('author')
    count_posts = posts_list.count()
    page_obj = paginate_page(request, posts_list)
    context = {
        'page_obj': page_obj,
        'author': author,
        'count_posts': count_posts,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    post_author = post.author
    post_count = post_author.posts.select_related('author').count()
    form = CommentForm(request.POST or None)
    comments = post.comments.select_related("author")
    context = {
        'post': post,
        'post_count': post_count,
        "comments": comments,
        "form": form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.user != author:
        return redirect('posts:post_detail', post_id)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    template = 'posts:post_detail'
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect(template, post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = paginate_page(request, post_list)
    context = {
        "page_obj": page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    template = 'posts:profile'
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect(template, username=username)


@login_required
def profile_unfollow(request, username):
    template = 'posts:profile'
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect(template, username=username)
