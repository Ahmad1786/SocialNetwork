
from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"), 
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),

    # api routes
    path("posts/", views.posts, name="posts"),
    path("newpage/", views.new_page, name="new_page"),
    path("update-following", views.update_following, name="update_following"),
    path("update-content/<int:post_id>", views.update_content, name="update_content"),
    path("like-or-unlike/<int:post_id>", views.like_or_unlike, name="like_or_unlike"),
    path("create-post", views.create_post, name="create_post")
]
