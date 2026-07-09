from django import forms
from .const import TYPE_REQUEST_USER
from .models import RequestUser


class RequestUserForm(forms.ModelForm):
    type_request = forms.CharField(
        widget=forms.RadioSelect(choices=TYPE_REQUEST_USER, attrs={
                                 'class': 'form__radio'}),
        initial='1')
    request_file = forms.FileField()
    request_message = forms.CharField(widget=forms.Textarea(attrs={'name':'body', 'rows':'6', 'cols':'25'}))

    class Meta:
        model = RequestUser
        fields = ['type_request']
