from django import forms
from .models import SavedReport
from django.utils.translation import gettext_lazy as _
from categories.models import Category


class DateRangeForm(forms.Form):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label=_("Start Date"),
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label=_("End Date"),
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(_("Start date cannot be after end date."))

        return cleaned_data


class ReportFilterForm(DateRangeForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-select"}),
        label=_("Categories"),
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields["categories"].queryset = Category.objects.filter(user=user)


class SaveReportForm(forms.ModelForm):
    class Meta:
        model = SavedReport
        fields = ["name", "report_type"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "report_type": forms.Select(attrs={"class": "form-select"}),
        }
