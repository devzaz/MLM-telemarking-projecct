from django import forms
from django.contrib.auth import get_user_model
from .models import Lead, LeadNote

User = get_user_model()

class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = ['name', 'email', 'phone', 'status', 'assigned_to', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # limit telemarketers in assigned_to dropdown
        try:
            self.fields['assigned_to'].queryset = User.objects.filter(role='telemarketer')
        except Exception:
            # in case role field differs or model not ready
            self.fields['assigned_to'].queryset = User.objects.all()

class LeadNoteForm(forms.ModelForm):
    class Meta:
        model = LeadNote
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add a short note...'}),
        }
