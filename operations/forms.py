from django import forms
from .models import Operation
from categories.models import Category


class OperationForm(forms.ModelForm):
    class Meta:
        model = Operation
        fields = ["category", "amount", "date", "description"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super(OperationForm, self).__init__(*args, **kwargs)
        if user:
            self.fields["category"].queryset = Category.objects.filter(user=user)
