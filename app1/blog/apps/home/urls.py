from django.urls import path

from .import views

app_name = "home"


urlpatterns = [
    path("", views.index, name = "index"),
    path("send_hot_request", views.send_hot_request, name = "send_hot_request"),
    path("send_request", views.send_request, name = "send_request"),
    path("thank_you", views.thank_you, name = "thank_you"),
    path("account", views.account, name = "account"),
]