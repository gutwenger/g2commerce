from datetime import datetime, timezone, tzinfo
from tzlocal import get_localzone

from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import AuctionListings, User, Category, Watchlist, Bids, Comments
from .forms import CreateListingForm
from .util import check_bid, get_watchlist_len


def index(request):
    user = request.user

    # Get all active listings
    entries = AuctionListings.objects.filter(removed=False, active=True).order_by("-start_date")
    watchlist_len = get_watchlist_len(user)

    # Check if already a bid
    entries = check_bid(entries)

    context = {
        "title": "active listings",
        "entries": entries,
        "watchlist_len": watchlist_len
    }

    return render(request, "auctions/index.html", context)


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
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


@login_required
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
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


@login_required
def my_items(request):
    user = user = request.user
    watchlist_len = get_watchlist_len(user)

    context = {
        "title": "my items",
        "watchlist_len": watchlist_len
    }

    entries = AuctionListings.objects.filter(lister=user).order_by("-start_date")
    entries = check_bid(entries)

    if entries:
        context["entries"] = entries
    else:
        context["no_entry_message"] = "Oops! You haven't created any bids!"
    
    return render(request, "auctions/index.html", context)


@login_required
def watchlist(request):
    user = request.user

    # If user tries access this page
    if request.method == "GET":
        watchlist_entries = Watchlist.objects.filter(user=user.id, item__removed=False).order_by("-item__start_date")
        watchlist_len = get_watchlist_len(user)

        context = {
            "title": "my watchlist",
            "watchlist_len": watchlist_len
        }

        # If there is entries
        if watchlist_entries:
            entries = []
            # Check if already a bid
            for watchlist_entry in watchlist_entries:
                current_bid = Bids.objects.filter(item__id=watchlist_entry.item.id).order_by("-bid_price")
                if current_bid:
                    setattr(watchlist_entry.item, "current_bid", current_bid[0].bid_price)
                entries.append(watchlist_entry.item)
            context["entries"] = entries
        # If no entry, return an error message
        else:
            context["no_entry_message"] = "Oops! You watchlist is empty!"

        return render(request, "auctions/index.html", context)

    # If user tries to add/remove item from watchlist
    elif request.method == "POST":
        item_id = request.POST["item"]
        entry = Watchlist.objects.filter(user=user.id, item_id=item_id)

        # If user tries to remove an item from watchlist
        if entry:
            entry.delete()
        # If user tries to add an item to watchlist
        else:
            listing = AuctionListings.objects.filter(id=item_id)[0]
            Watchlist.objects.create(user=user, item=listing)

        return HttpResponseRedirect(reverse('listing', args=[item_id]))


@login_required
def my_bids(request):
    user = user = request.user
    watchlist_len = get_watchlist_len(user)
    user_bids = Bids.objects.filter(bidder=user, item__removed=False).order_by("-item__start_date")
    entries = []

    for user_bid in user_bids:
        if user_bid.item not in entries:
            entries.append(user_bid.item)

    entries = check_bid(entries)

    context = {
        "title": "my bids",
        "watchlist_len": watchlist_len
    }

    if entries:
        context["entries"] = entries
    else:
        context["no_entry_message"] = "Oops! You haven't made any bids!"

    return render(request, "auctions/index.html", context)


@login_required
def won_bids(request):
    user = user = request.user
    watchlist_len = get_watchlist_len(user)
    user_bids = Bids.objects.filter(bidder=user, item__active=False).order_by("-item__start_date")
    user_bids_items = []
    entries = []

    context = {
        "title": "won bids",
        "watchlist_len": watchlist_len
    }

    # Get unique ids of all user's bids
    for user_bid in user_bids:
        if user_bid.item not in user_bids_items:
            user_bids_items.append(user_bid.item)

    # Check if user wins any bids
    for user_bids_item in user_bids_items:
        item = Bids.objects.filter(item=user_bids_item).order_by('bid_price')
        if item[0].bidder == user:
            entries.append(item[0].item)

    if entries:
        context["entries"] = check_bid(entries)
    else:
        context["no_entry_message"] = "Oops! You haven't won any bids!"

    return render(request, "auctions/index.html", context)


@login_required
def create_listing(request):
    user = request.user
    # If user tries to access
    if request.method == "GET":
        form = CreateListingForm()
        categories = Category.objects.all().order_by('category')
        watchlist_len = get_watchlist_len(user)
        context = {
            "form": form,
            "categories": categories,
            "watchlist_len": watchlist_len
        }
        return render(request, "auctions/create_listing.html", context)

    # If user submit a form
    else:
        name = request.POST["name"]
        category = Category.objects.filter(category=request.POST["category"])[0]
        start_price = request.POST["start_price"]
        start_price = "{:,}".format(float(start_price))
        description = request.POST["description"]
        lister = User.objects.filter(username=request.POST["lister"])[0]
        start_date = datetime.now(get_localzone()).strftime("%Y-%m-%d %H:%M:%S")
        removed = False
        active = True

        photo = request.FILES['photo']
        print(photo)

        listing_entry = AuctionListings.objects.create(name=name, lister=lister, start_price=start_price, start_date=start_date, category=category, description=description, photo=photo, removed=removed, active=active)
        listing_entry.save()

        return HttpResponseRedirect(reverse("index"))


def categories(request):
    user = request.user
    categories = Category.objects.all().order_by('category')
    watchlist_len = get_watchlist_len(user)
    
    context = {
        "categories": categories,
        "watchlist_len": watchlist_len
    }

    return render(request, "auctions/categories.html", context)


def all_categories(request, cat):
    user = request.user
    watchlist_len = get_watchlist_len(user)
    categories = Category.objects.filter(category=cat.lower().capitalize())

    # If no entry
    if not categories:
        context = {
            "title": "categories: ERROR",
            "no_entry_message": "Oops! Error, no such category",
            "watchlist_len": watchlist_len
        }
        return render(request, "auctions/index.html", context)

    entries = AuctionListings.objects.filter(category=categories[0].id, removed=False, active=True).order_by("-start_date")
    
    # Check if already a bid
    entries = check_bid(entries)

    context = {
        "title": f"categories: {cat.lower().capitalize()}",
        "entries": entries,
        "watchlist_len": watchlist_len
    }
    
    return render(request, "auctions/index.html", context)


def listing(request, number):
    user = request.user
    entry = AuctionListings.objects.filter(id=number)

    # If no such entry
    if not entry:
        context = {
                "search": search,
                "error": "NO RESULT"
            }
        return render(request, "auctions/listing.html", context)

    user = request.user
    watchlist_item = Watchlist.objects.filter(user=user.id, item=entry[0])
    watchlist_len = get_watchlist_len(user)

    context = {
        "entry": entry[0],
        "user": user,
        "watchlist_len": watchlist_len
    }

    # Check if already a bid
    bid_info = Bids.objects.filter(item=entry[0]).order_by("-bid_price")
    if bid_info:
        profit = float(bid_info[0].bid_price.replace(",", "")) - float(entry[0].start_price.replace(',', ''))
        context["bid_info"] = bid_info[0]
        context["profit"] = "{:,}".format(float(profit))
        context["bid_winner"] = bid_info[0].bidder

    # Check if there are comments
    comments = Comments.objects.filter(item=entry[0]).order_by("-time")
    if comments:
        context["comments"] = comments

    # Check if the item is in watchlist
    if watchlist_item:
        context["watchlist"] = True

    return render(request, "auctions/listing.html", context)


def search(request):
    user = request.user
    watchlist_len = get_watchlist_len(user)

    # If user query for an item
    if request.method == "POST":
        
        search = request.POST["search-item"]
        entries = AuctionListings.objects.filter(name__icontains=search, removed=False, active=True)

        # If no entry
        if not entries:
            context = {
                "title": "search",
                "search": search,
                "watchlist_len": watchlist_len,
                "no_entry_message": "Oops! Error! No result!"
            }
            return render(request, "auctions/index.html", context)

        # Check if already a bid
        entries = check_bid(entries)

        context = {
            "title": "search",
            "search": search,
            "entries": entries,
            "watchlist_len": watchlist_len
        }

        if len(entries) == 1:
            context["search_result"] = len(entries)
        else:
            context["search_results"] = len(entries)

        return render(request, "auctions/index.html", context)


def bid(request):
    user = request.user
    watchlist_len = get_watchlist_len(user)

    # If user submits a bid
    if request.method == "POST":
        # Get the bid price
        bid_price = request.POST["bid_price"]
        item_id = request.POST["item_id"]

        # Get the item
        item = AuctionListings.objects.get(id__exact=item_id)

        # If no such entry
        if not item:
            context = {
                "search": search,
                "watchlist_len": watchlist_len,
                "error": "NO RESULT"
            }
            return render(request, "auctions/listing.html", context)

        # Check if there is already a bid
        bided = Bids.objects.filter(item__id=item_id).order_by("-bid_price")
        bid_time = datetime.now(get_localzone()).strftime("%Y-%m-%d %H:%M:%S")

        context = {
            "item_id": item_id,
            "watchlist_len": watchlist_len,
            "bid_message": True
        }

        # If already a bid, check if the bid_price is larger than currenty bid
        if bided and float(bid_price) <= float(bided[0].bid_price.replace(",", "")):
            context["bid_message"] = "Bid must be larger than the current bid."
            return render(request, "auctions/bid.html", context)
        
        # If no bid has ever been placed
        if not bided:
            if bid_price <= item.start_price:
                context["bid_message"] = "Bid must be larger than the starting bid."
                return render(request, "auctions/bid.html", context)

        # Create a bid
        bid_price = "{:,}".format(float(bid_price))
        Bids.objects.create(item=item, bidder=user, bid_price=bid_price, bid_time=bid_time)

        return render(request, "auctions/bid.html", context)


def end_bid(request):
    # If user submits an end_bid request
    if request.method == "POST":
        print("RECEIVE END BID REQUEST")
        # User action
        item_id = request.POST["item_id"]
        action = request.POST["lister_action"]

        # Get the item
        item = AuctionListings.objects.get(id=item_id)
        print(item)

        # If user tries to remove a bid
        if action == "remove_bid":
            # Set the item as removed
            item.removed = True
            item.save()
        
        # If user tries to close the bid
        else:
            # Deactivate the item
            item.active = False
            item.save()

    return HttpResponseRedirect(reverse('listing', args=[item_id]))


def comment(request):
    user = request.user
    time = datetime.now(get_localzone()).strftime("%Y-%m-%d %H:%M:%S")
    # If user submits a comment
    if request.method == "POST":
        item_id = request.POST["item_id"]
        comments = request.POST["comment"]

        # Get the item
        item = AuctionListings.objects.get(id=item_id)

        new_comment = Comments.objects.create(user=user, time=time, item=item, comments=comments)
        new_comment.save()

        return HttpResponseRedirect(reverse('listing', args=[item_id]))
        

def all_user_items(request, user_name):
    user = request.user
    watchlist_len = get_watchlist_len(user)
    search_user = User.objects.get(username=user_name);

    # Context to be returned
    context = {
            "title": f"User: {search_user.username}",
            "watchlist_len": watchlist_len,
        }

    # Get all entries of specific user
    entries = AuctionListings.objects.filter(lister=search_user, removed=False, active=True).order_by("-start_date")

    # If no entry
    if not entries:
        context["no_entry_message"] = "This user hasn't post anything yet."

    else:
        context["entries"] = check_bid(entries)
    
    return render(request, "auctions/index.html", context)
