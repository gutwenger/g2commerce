from .models import *

def get_context(user):
    watchlist_len = get_watchlist_len(user)

def check_bid(active_listings):
    entries = active_listings
    for i, entry in enumerate(entries):
        current_bid = Bids.objects.filter(item__id=entry.id).order_by("-bid_price")
        if current_bid:
            setattr(entry, "current_bid", current_bid[0].bid_price)
    return entries

def get_watchlist_len(user):
    user_watchlists = Watchlist.objects.filter(user=user.id)
    watchlist_items = []

    for user_watchlist in user_watchlists:
        if not user_watchlist.item.removed:
            watchlist_items.append(user_watchlist)
    
    number_of_watchlist_items = len(watchlist_items)

    return number_of_watchlist_items