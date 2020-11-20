from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Comment, Follow

@cache_page(20)
def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {"page": page, "paginator": paginator}
    return render(request, "index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {"group": group, "page": page, "paginator": paginator}
    return render(request, "group.html", context)


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect("index")
    return render(request, "new_post.html", {"form": form})

def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "profile.html",
                  {"page": page, "paginator": paginator, "author": author})

def post_view(request, username, post_id): 
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(author.posts.all(), pk=post_id)
    form = CommentForm()
    comments = post.comments.all()
    return render(request, "post.html", {"post": post, "author": author, "form": form, "comments": comments})

def post_edit(request, username, post_id):
    user = get_object_or_404(User, username=username)
    if request.user != user:
        return redirect("post_detail", username=username, post_id=post_id)
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect("post_detail", username=username, post_id=post.pk)
    return render(request, "new_post.html", {"form": form, "post": post})

@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id) #ищем пост, id которого соответсвует нашему
    form = CommentForm(request.POST or None, instance=post) #передаём в форму наш POST-запрос
    comments = post.comments.all() #собираем комментарии, относящиеся к найденному посту, comments - related_name
    if request.method == "POST" and form.is_valid():
        form = CommentForm(request.POST)
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect("post_detail", username=post.author, post_id = post_id)
    return render(request, "post.html", {"form": form, "post": post, "comments": comments})

def page_not_found(request, exception):
    return render(
        request, 
        "misc/404.html", 
        {"path": request.path}, 
        status=404
    )

def server_error(request):
    return render(request, "misc/500.html", status=500)

@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, 
        'follow.html', 
        {'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    following = author.following.exists()
    if author != user and not following:
        Follow.objects.get_or_create(user=user, author=author)
        #return redirect("profile", username)
    return render(request, "profile.html", {'following': following})

@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if author != user:
        Follow.objects.get(user=user, author=author).delete()
    return redirect("profile", username)