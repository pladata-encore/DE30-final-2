from django import forms
from .models import UserPreferences, Region, Subregion

class UserPreferencesForm(forms.ModelForm):
    class Meta:
        model = UserPreferences
        fields = ['region', 'subregion', 'start_date', 'end_date', 'pets_allowed', 'pet_size', 'preferred_foods', 'preferred_activities', 'preferred_accommodation']
        widgets = {
            'region': forms.Select(attrs={'id': 'region', 'class': 'form-control'}),
            'subregion': forms.Select(attrs={'id': 'subregion', 'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'id': 'start_date', 'class': 'form-control datepicker', 'readonly': True}),
            'end_date': forms.DateInput(attrs={'id': 'end_date', 'class': 'form-control datepicker', 'readonly': True}),
            'pets_allowed': forms.Select(attrs={'id': 'pets_allowed', 'class': 'form-control', 'onchange': 'togglePetSize(this.value)'}),
            'pet_size': forms.Select(attrs={'id': 'pet_size', 'class': 'form-control'}),
            'preferred_foods': forms.HiddenInput(),
            'preferred_activities': forms.HiddenInput(),
            'preferred_accommodation': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pet_size'].required = False
