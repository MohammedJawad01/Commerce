from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Category, Listing , Comment, Bid


def index(request):
    activeList = Listing.objects.filter(isActive = True)
    categories = Category.objects.all()
    return render(request, "auctions/index.html",{
        "List" : activeList,
        "categories":categories
    })

def closeAuction(request ,id):
    listingData = Listing.objects.get(pk = id )
    listingData.isActive = False
    listingData.save()
    listingInWatchlist = request.user in listingData.watchlist.all()
    Comments = Comment.objects.filter(listing=listingData)
    isOwner = request.user.username == listingData.owner.username
    return render(request , "auctions/listing.html",{
        "listing" : listingData,
        "listingInWatchlist":listingInWatchlist,
        "Comments":Comments,
        "isOwner": isOwner,
        "update":True,
        "message":"congratulations the deal is closed"
    })


def listing(request, id):
    listingData = Listing.objects.get(pk=id)
    # I have to check if the item in the watchlist
    listingInWatchlist = request.user in listingData.watchlist.all()
    Comments = Comment.objects.filter(listing=listingData)
    isOwner = request.user.username == listingData.owner.username
    return render(request , "auctions/listing.html",{
        "listing" : listingData,
        "listingInWatchlist":listingInWatchlist,
        "Comments":Comments,
        "isOwner": isOwner
    })

def addBid(request, id):
    newBid = request.POST["newBid"]
    listingData = Listing.objects.get(pk=id)
    listingInWatchlist = request.user in listingData.watchlist.all()
    Comments = Comment.objects.filter(listing=listingData)
    isOwner = request.user.username == listingData.owner.username
    if int(newBid) > listingData.price.bid:
        updateBid = Bid(user = request.user , bid = int(newBid))
        updateBid.save()
        listingData.price = updateBid
        listingData.save()
        return render (request , "auctions/listing.html",{
            "listing" : listingData,
            "message":"Bid successfully applied",
            "update": True,
            "listingInWatchlist":listingInWatchlist,
            "Comments":Comments,
            "isOwner": isOwner
        })
    else:
            return render (request , "auctions/listing.html",{
            "listing" : listingData,
            "message":"Bid Failed",
            "update": False,"listingInWatchlist":listingInWatchlist,
            "Comments":Comments,
            "isOwner": isOwner
        })


def removeWatchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    currentUser = request.user
    listingData.watchlist.remove(currentUser)
    return HttpResponseRedirect (reverse("listing", args=(id, )))

def addWatchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    currentUser = request.user
    listingData.watchlist.add(currentUser)
    return HttpResponseRedirect (reverse("listing", args=(id, )))

def watchlistDisplay(request):
    currentUser = request.user
    listing = currentUser.watchlist.all()
    return render( request , "auctions/watchlist.html",{
        "listing":listing
    })

def categoryDisplay(request):
    if request.method == "POST":
        categoryFromForm = request.POST["category"]
        category = Category.objects.get(categoryName = categoryFromForm)
        activeList = Listing.objects.filter(isActive = True,category = category)
        categories = Category.objects.all()
        return render(request, "auctions/index.html",{
            "List" : activeList,
            "categories":categories
        })
    
def addComment(request , id):
    currentUser = request.user
    listingData = Listing.objects.get(pk=id)
    message = request.POST["newComment"]

    newComment = Comment (
        author = currentUser,
        listing = listingData,
        message =message
    )

    newComment.save()

    return HttpResponseRedirect (reverse("listing", args=(id, )))


def createListing(request):
    if request.method == "GET":
        # calling the categories from the database so i can send them to the html so i can make selection
        categories = Category.objects.all()
        return render (request, "auctions/create.html",{
            "categories":categories
        })
    
    else :
        # i have to get the data from the form
        title = request.POST["title"]
        description = request.POST["description"]
        imageUrl = request.POST["imageUrl"]
        price = request.POST["price"]
        category = request.POST["category"]

        # i have to get the user so every list connect to a user 
        # i am using this because no one is allowed to create list only if he loged in
        currentUser = request.user

        # i have to get the data from the category
        categoryData = Category.objects.get(categoryName = category)

        # create a bid object 
        bid = Bid(bid=float(price), user= currentUser)
        bid.save()

        # for the new list the left is from models and right form above
        newList= Listing(
            title=title,
            description=description,
            imageUrl=imageUrl,
            price=bid,
            owner=currentUser,
            category=categoryData           
        )
        # i have to save the data
        newList.save()
        # i have to redirect the user to the index
        return HttpResponseRedirect(reverse("index"))


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
