from django.contrib import admin

#from blog.apps.articles.models import Article

from .models import Menu, Slider, Client,Order, RequestUser

admin.site.register(Menu)
admin.site.register(Slider)
admin.site.register(Client)
admin.site.register(Order)
admin.site.register(RequestUser)
#admin.site.register(Article)