from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse_lazy, reverse
from .forms import UserCreationFormCustom
from django.views.generic.edit import CreateView
from home.models import Client

class SignUp(CreateView):
    form_class = UserCreationFormCustom
    success_url = reverse_lazy("login")
    template_name = "users/signup.html"

    def form_valid(self, form):
        fields = form.save(commit=False)
        email_from_hot_request = self.request.session.get('email_from_hot_request','')
        if email_from_hot_request:
            fields.email = email_from_hot_request
        else:
            client = Client(client_name=fields.username, client_mail = fields.email)
            client.save()

        fields.save()
        return super().form_valid(form)