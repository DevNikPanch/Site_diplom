from django.urls import path

from .import views

app_name = "home"


urlpatterns = [
    path("", views.index, name = "index"),
    path("send_hot_request", views.send_hot_request, name = "send_hot_request"),
    path("send_request", views.send_request, name = "send_request"),
    path("thank_you", views.thank_you, name = "thank_you"),
    path("account", views.account, name = "account"),
    path('meter/<int:meter_id>/deactivate/', views.deactivate_meter, name='deactivate_meter'),
    path('meter/<int:meter_id>/reading/', views.submit_reading, name='submit_reading'),
    path('meter/<int:meter_id>/history/', views.meter_history, name='meter_history'),
]