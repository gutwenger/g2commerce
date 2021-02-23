from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    pass


class Category(models.Model):
    category = models.CharField(max_length=32)

    def __str__(self):
        return f"{self.category}"


class AuctionListings(models.Model):
    name = models.CharField(max_length=120)
    lister = models.ForeignKey(User, on_delete=models.CASCADE)
    start_price = models.CharField(max_length=20)
    start_date = models.DateTimeField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.CharField(max_length=640)
    photo = models.ImageField(upload_to="media")
    removed = models.BooleanField()
    active = models.BooleanField()

    def __str__(self):
        return f"[{self.id}][{self.category}] {self.name}"


class Bids(models.Model):
    item = models.ForeignKey(AuctionListings, on_delete=models.CASCADE)
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    bid_price = models.CharField(max_length=20)
    bid_time = models.DateTimeField()


class Comments(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    time = models.DateTimeField()
    item = models.ForeignKey(AuctionListings, on_delete=models.CASCADE)
    comments = models.CharField(max_length=250)


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(AuctionListings, on_delete=models.CASCADE)
