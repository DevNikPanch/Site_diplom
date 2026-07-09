from django.urls import path

from .import views

app_name = "articles"


urlpatterns = [
    path("", views.index, name = "index"),
    path('section/<int:article_id>', views.section, name ='section'),
    path('add_comment/<int:article_id>', views.add_comment, name ='add_comment')
]