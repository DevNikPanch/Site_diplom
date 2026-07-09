from http import client
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from .forms import RequestUserForm
from .models import Slider, Client, RequestUser
from django.contrib.auth.models import User


def index(request):
    slides = Slider.objects.order_by('slider_queue')
    return render(request, "home/list.html", {'slides': slides, "first_slide": slides.first()})


def thank_you(request):
    return render(request, 'home/detail.html')


def send_hot_request(request):
    client = Client()
    client.client_name = request.POST["name"]
    client.client_mail = request.POST["email"]
    client.save()
    Client.objects.get(id=client.id).order_set.create(order_object=request.POST["subject"],
                                                      order_address=request.POST['address'],
                                                      order_text=request.POST["message"])

    request.session['email_from_hot_request'] = request.POST["email"]
    return HttpResponseRedirect(reverse('home:thank_you'))


def account(request):

    if request.user.is_authenticated:
        form = RequestUserForm()
        user = User.objects.get(id=request.user.id)
        client = Client.objects.get(client_mail=user.email)
        return render(request, "home/account.html", {"form": form, "data": client.get_full_info()})
    return HttpResponseRedirect(reverse("login"))


def send_request(request):
    request_user = RequestUser(user=User.objects.get(id=request.user.id),
                               request_file=request.FILES['request_file'],
                               request_message=request.POST['request_message'],
                               type_request=request.POST['type_request'],
                               )
    request_user.save()
    return HttpResponseRedirect(reverse("home:account"))
