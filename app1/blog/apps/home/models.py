from django.db import models
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.utils import timezone
from .const import TYPE_REQUEST_USER, TYPE_REQUEST_STATUS


class Menu(models.Model):
    menu_url = models.CharField("Ссылка меню", max_length=200)
    menu_text = models.CharField("Текст меню", max_length=50)

    class Meta:
        verbose_name = 'Меню'
        verbose_name_plural = 'Меню'

    def __str__(self):
        return self.menu_text


class Slider(models.Model):
    slider_url = models.CharField("Ссылка слайдера", max_length=200, null=True)
    slider_queue = models.IntegerField("Очередь слайда")
    slider_delay = models.IntegerField("Задержка слайда")

    class Meta:
        verbose_name = 'Слайдер'
        verbose_name_plural = 'Слайдер'


class Client(models.Model):
    client_name = models.CharField(
        "Имя пользователя", max_length=200, null=True)
    client_mail = models.EmailField(
        "Почта пользователя", max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def __str__(self):
        return f"{self.client_name}-{self.client_mail}"

    def try_get_user_by_client_email(self):
        return User.objects.get(email=self.client_mail)

    def get_full_info(self):
        user = self.try_get_user_by_client_email()
        client = Client.objects.get(id=self.id)
        if(user):
            return {"client": self, "user": user, "orders": client.order_set.all(), "requests_user": user.requestuser_set.all()}
        else:

            return {"client": self, "orders": client.order_set.all()}


class Order(models.Model):
    order_object = models.CharField(
        "Объект договора", max_length=200, null=True)
    order_text = models.CharField("Текст договора", max_length=200, null=True)
    order_address = models.CharField(
        "Адрес договора", max_length=200, null=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    def __str__(self):
        return self.order_object

    class Meta:
        verbose_name = "Договор"
        verbose_name_plural = "Договора"


class RequestUser(models.Model):
    id = models.BigAutoField(primary_key=True)

    def order_directory_path(instance, filename):

        return 'order/{1}'.format(instance.id, filename)

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    request_file = models.FileField(
        upload_to=order_directory_path, max_length=254)
    date = models.DateTimeField("Дата создания", default=timezone.now)

    request_message = models.TextField("Сообщение заявления", max_length=200)
    type_request = models.CharField(
        choices=TYPE_REQUEST_USER,
        max_length=1,
        verbose_name='Тип заявки'
    )
    type_status = models.CharField(
        choices=TYPE_REQUEST_STATUS,
        max_length=1,
        verbose_name='Статус заявки',
        default='1'
    )


    class Meta:
        verbose_name = "Заявка пользователя"
        verbose_name_plural = "Заявки пользователей"