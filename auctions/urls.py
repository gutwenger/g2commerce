from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("my_bids", views.my_bids, name="my_bids"),
    path("create_listing", views.create_listing, name="create_listing"),
    path("categories", views.categories, name="categories"),
    path("category/<str:cat>", views.all_categories, name="all_categories"),
    path("search", views.search, name="search"),
    path("listing/<str:number>", views.listing, name="listing"),
    path("bid", views.bid, name="bid"),
    path("end_bid", views.end_bid, name="end_bid"),
    path("won_bids", views.won_bids, name="won_bids"),
    path("my_items", views.my_items, name="my_items"),
    path("comment", views.comment, name="comment"),
    path("user/<str:user_name>", views.all_user_items, name="all_user_items")
]
