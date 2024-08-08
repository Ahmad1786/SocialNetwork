from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    pass

class Post(models.Model):
    poster = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add = True)
    likes = models.ManyToManyField(User, related_name='liked_posts')

    def __str__(self):
        return f"{self.poster.username} on {self.created_on}"
    
    def serialize(self):
        return {
            "id": self.id,
            "poster": self.poster.username,
            "content": self.content,
            "likes": self.likes.count(),
            "created_on": self.created_on
        }

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_on = models.DateTimeField(auto_now_add = True)

    class Meta:
        unique_together = ('follower', 'followed')

    def __str__(self):
        return f"{self.follower.username} following {self.followed.username}"