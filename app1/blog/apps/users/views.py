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

    # Функция для кастомной валидации полей формы модели
    def form_valid(self, form):
        # создаем форму, но не отправляем его в БД, пока просто держим в памяти
        fields = form.save(commit=False)
        email_from_hot_request = self.request.session.get('email_from_hot_request','')
        # Если есть email с формы на главной, то подставляем её, 
        # иначе создаём нового клиента  на основе данных о user
        if email_from_hot_request:
            fields.email = email_from_hot_request
        else:
            client = Client(client_name=fields.username, client_mail = fields.email)
            client.save()

        # Наконец сохраняем в БД
        fields.save()
        return super().form_valid(form)