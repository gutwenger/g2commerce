from django import forms
from .models import *

class CreateListingForm(forms.ModelForm):

    class Meta:
        model = AuctionListings
        fields = ['name', 'start_price', 'category', 'description', 'photo']