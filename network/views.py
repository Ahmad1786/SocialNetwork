from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Post, Follow
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET, require_http_methods
import json
from django.http import JsonResponse


def index(request):
    if not request.user.is_authenticated:
        return render(request, "network/index.html")
    
    all_posts = Post.objects.all().order_by('-created_on')
    paginator = Paginator(all_posts, 10) # page1 = paginator.page(1)
    curr = 1 # always start at page 1

    context = {
        "paginator": paginator,
        "page_x": paginator.get_page(curr),
        "curr": curr,
        "posts_label": "All Posts",
        "posts_label_type": "all",
        # "index": True
    }
    
    return render(request, "network/index.html", context)

@require_GET
def posts(request):
    if not request.user.is_authenticated:
        return HttpResponse("NOT ALLOWED -> NEED TO LOG IN")
    
    query_type = request.GET.get('type', None)

    # all / following / profile
    if query_type == 'all':
        all_posts = Post.objects.all().order_by('-created_on')
        posts_label = "All Posts"
        posts_label_type = 'all'
    elif query_type == 'following':
        following = [f.followed for f in request.user.following.all()]
        all_posts = Post.objects.filter(poster__in=following).order_by('-created_on')
        posts_label = "Posts from following"
        posts_label_type = 'following'
    elif query_type == 'profile':
        user_id = request.GET.get('user')
        user = User.objects.filter(pk=user_id).first()
        all_posts = Post.objects.filter(poster=user).order_by('-created_on')
        posts_label_type = f"profile-{user.pk}"
        if request.user == user:
            posts_label = "Your Posts"
        else:
            posts_label = f"Posts from {user.username}"
    
    paginator = Paginator(all_posts, 10) # page1 = paginator.page(1)
    curr = 1 # always start at page 1

    context = {
        "paginator": paginator,
        "page_x": paginator.get_page(curr),
        "curr": curr,
        "posts_label": posts_label,
        "posts_label_type": posts_label_type
    }

    if query_type == 'profile':
        context["on_profile_page"] = True
        context["viewing_someone_else"] = request.user != user
        context["user"] = user
        context["follow_string"] = ("Unfollow" if Follow.objects.filter(follower=request.user, followed=user).exists() else "Follow")
        context["action"] = ("DELETE" if Follow.objects.filter(follower=request.user, followed=user).exists() else "POST")

    return render(request, "network/posts.html", context)

def new_page(request):
    if not request.user.is_authenticated:
        return HttpResponse("NOT ALLOWED -> NEED TO LOG IN")
    
    current_page = int(request.GET.get('curr', None))
    direction = request.GET.get('direction', None)
    
    if direction == 'next': 
        new_page = current_page + 1
    elif direction == 'prev': 
        new_page = current_page - 1
    
    ## COPYING CODE
    # all / following / profile
    query_type = request.GET.get('type', None)

    if query_type == 'all':
        all_posts = Post.objects.all().order_by('-created_on')
        posts_label = "All Posts"
        posts_label_type = 'all'
    elif query_type == 'following':
        following = [f.followed for f in request.user.following.all()]
        all_posts = Post.objects.filter(poster__in=following).order_by('-created_on')
        posts_label = "Posts from following"
        posts_label_type = 'following'
    elif query_type == 'profile':
        user_id = request.GET.get('user')
        user = User.objects.filter(pk=user_id).first()
        all_posts = Post.objects.filter(poster=user).order_by('-created_on')
        posts_label_type = f"profile-{user.pk}"
        if request.user == user:
            posts_label = "Your Posts"
        else:
            posts_label = f"Posts from {user.username}"
    
    paginator = Paginator(all_posts, 10) 
    page_x = paginator.get_page(new_page)

    context = {
        "paginator": paginator,
        "page_x": page_x,
        "curr": new_page,
        "posts_label": posts_label,
        "posts_label_type": posts_label_type,
    }

    if query_type == 'profile':
        context["on_profile_page"] = True
        context["viewing_someone_else"] = request.user != user
        context["user"] = user
        context["follow_string"] = ("Unfollow" if Follow.objects.filter(follower=request.user, followed=user).exists() else "Follow")
        context["action"] = ("DELETE" if Follow.objects.filter(follower=request.user, followed=user).exists() else "POST")
    
    
    return render(request, "network/posts.html", context)

@require_http_methods(["POST", "DELETE"])
def update_following(request):
    data = json.loads(request.body)
    user_id = data["user"]
    if request.method == "POST":
        user = User.objects.filter(pk=user_id).first()
        f = Follow(follower=request.user, followed=user)
        f.save()
        return JsonResponse({"message": "Followed successfully", "follow_string": "Unfollow", "new_count": user.followers.count()})

    # delete follow
    user = User.objects.filter(pk=user_id).first()
    Follow.objects.filter(follower=request.user, followed=user).delete()
    return JsonResponse({"message": "Unfollowed successfully", "follow_string": "Follow", "new_count": user.followers.count()})

@require_http_methods(["PATCH"])
def update_content(request, post_id):
    # For security, ensure ... it is not possible for a user via any route, to edit another user’s posts.
    post = Post.objects.filter(pk=post_id).first()
    
    if post.poster != request.user:
        return JsonResponse({"message": "Not allowed to edit someone else post..."}, status=403)

    data = json.loads(request.body)
    new_content = data['newContent']
    post.content = new_content
    post.save()
    return JsonResponse({"message": "Content updated successfully...", "new_content": post.content})

@require_http_methods(["PATCH"])
def like_or_unlike(request, post_id):
    post = Post.objects.filter(pk=post_id).first()
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        return JsonResponse({"message": "Unliked successfully...", "new_count": post.likes.count()})
    else:
        post.likes.add(request.user)
        return JsonResponse({"message": "Liked successfully...", "new_count": post.likes.count()})


@require_http_methods(["POST"])
def create_post(request):
    data = json.loads(request.body)
    post_content = data['content']
    post = Post.objects.create(poster=request.user, content=post_content)
    post.save()

    return JsonResponse({"message": "Created successfully...", "user_id": request.user.id}, status=201)

    
def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")