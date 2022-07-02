from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post, Follow


POSTS_ON_VIEW: int = 10


def paginator(request, posts):
    return Paginator(posts, POSTS_ON_VIEW).get_page(request.GET.get('page'))


def index(request):
    return render(request, 'posts/index.html', {
        'page_obj': paginator(request, Post.objects.all()),
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': paginator(request, group.posts.all()),
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following: bool = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=User.objects.get(username=username)
        ).exists()
    return render(request, 'posts/profile.html', {
        'page_obj': paginator(request, author.posts.all()),
        'author': author,
        'following': following
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'form': CommentForm(request.POST or None),
        'comments': post.comments.all()
    })


@login_required
def post_create(request):
    post_form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if post_form.is_valid():
        post = post_form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': post_form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:index')
    post_form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if post_form.is_valid():
        post_form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/create_post.html', {
        'form': post_form,
        'post': post,
    })

@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id)

@login_required
def follow_index(request):
    following = Follow.objects.filter(user=request.user).values_list('author', flat=True)
    return render(request, 'posts/follow.html', {
        'page_obj': paginator(request, Post.objects.filter(author__in=following)),
    })

@login_required
def profile_follow(request, username):
    if request.user == User.objects.get(username=username):
        return redirect('posts:profile', username)
    if Follow.objects.filter(
        user=request.user,
        author=User.objects.get(username=username)
    ).exists():
        return redirect('posts:profile', username)
    Follow.objects.create(
        user=request.user,
        author=User.objects.get(username=username)
    )
    return redirect('posts:profile', username)

@login_required
def profile_unfollow(request, username):
    if request.user.username == username:
        return redirect('posts:profile', username)
    Follow.objects.filter(
        user=request.user,
        author=User.objects.get(username=username)
    ).delete()
    return redirect('posts:profile', username)
