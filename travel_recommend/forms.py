from django import forms
from .models import UserPreferences, Region, Subregion

class UserPreferencesForm(forms.Form):
    region = forms.CharField(max_length=100)
    subregion = forms.CharField(max_length=100)
    start_date = forms.DateField()
    end_date = forms.DateField()
    food_preference = forms.CharField(widget=forms.Textarea)
    tour_type = forms.CharField(widget=forms.Textarea)
    accommodation_type = forms.CharField(widget=forms.Textarea)
    travel_preference = forms.CharField(max_length=100)
    food_detail = forms.CharField(widget=forms.Textarea, required=False)
    activity_detail = forms.CharField(widget=forms.Textarea, required=False)
    accommodation_detail = forms.CharField(widget=forms.Textarea, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
