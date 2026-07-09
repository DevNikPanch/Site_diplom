import random

from django.db import models
from django.contrib.auth.models import User
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
    client_name = models.CharField("Имя пользователя", max_length=200, null=True)
    client_mail = models.EmailField("Почта пользователя", max_length=50, null=True, blank=True)

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
        if user:
            return {"client": self, "user": user, "orders": client.order_set.all(),
                    "requests_user": user.requestuser_set.all()}
        else:
            return {"client": self, "orders": client.order_set.all()}


class Order(models.Model):
    order_object = models.CharField("Объект договора", max_length=200, null=True)
    order_text = models.CharField("Текст договора", max_length=200, null=True)
    order_address = models.CharField("Адрес договора", max_length=200, null=True)
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
    request_file = models.FileField(upload_to=order_directory_path, max_length=254)
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


class SettingsTariff(models.Model):
    SERVICE_CHOICES = [
        ('water', 'Холодное водоснабжение'),
        ('sewerage', 'Водоотведение'),
        ('hot_water', 'Горячее водоснабжение'),
    ]
    service_type = models.CharField(
        "Тип услуги",
        max_length=20,
        choices=SERVICE_CHOICES,
        unique=True
    )
    price_per_unit = models.DecimalField("Цена за единицу (руб/м³)", max_digits=10, decimal_places=2)
    valid_from = models.DateField("Действует с")
    valid_until = models.DateField("Действует по", null=True, blank=True)

    class Meta:
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифы"
        ordering = ['service_type', '-valid_from']
        db_table = 'settings_tariff'

    def __str__(self):
        return f"{self.get_service_type_display()} — {self.price_per_unit} руб. (с {self.valid_from})"

class SiteSettings(models.Model):
    reading_start_day = models.PositiveSmallIntegerField(
        "День начала приёма показаний",
        default=20,
        help_text="Число месяца, с которого разрешена подача показаний"
    )
    reading_end_day = models.PositiveSmallIntegerField(
        "День окончания приёма показаний",
        default=25,
        help_text="Число месяца, до которого разрешена подача (включительно)"
    )

    allow_multiple_readings = models.BooleanField(
        "Разрешить несколько подач в периоде",
        default=False,
        help_text="Если отключено, пользователь может подать показания только 1 раз за период"
    )

    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self):
        return "Глобальные настройки"

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def is_reading_allowed(self):
        today = timezone.now().date().day
        return self.reading_start_day <= today <= self.reading_end_day

class AccountRequest(models.Model):
    class RequestStatus(models.TextChoices):
        PENDING = 'pending', 'На рассмотрении'
        APPROVED = 'approved', 'Одобрена'
        REJECTED = 'rejected', 'Отклонена'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='account_requests')
    
    full_name = models.CharField("ФИО заявителя", max_length=200)
    phone = models.CharField("Контактный телефон", max_length=20)
    address = models.CharField("Адрес помещения", max_length=300)
    
    APPLICANT_CHOICES = [
        ('individual', 'Физическое лицо'),
        ('legal_entity', 'Юридическое лицо / ИП'),
    ]
    applicant_type = models.CharField(
        "Тип заявителя",
        max_length=20,
        choices=APPLICANT_CHOICES,
        default='individual'
    )

    company_name = models.CharField("Наименование организации", max_length=300, blank=True, null=True)
    inn = models.CharField("ИНН", max_length=12, blank=True, null=True)
    kpp = models.CharField("КПП", max_length=9, blank=True, null=True)
    manager_position = models.CharField("Должность руководителя", max_length=150, blank=True, null=True)

    ownership_document = models.FileField("Правоустанавливающий документ (ЕГРН/договор)", upload_to='account_requests/%Y/%m/')
    passport_copy = models.FileField("Копия паспорта", upload_to='account_requests/%Y/%m/')
    snils_copy = models.FileField("Копия СНИЛС", upload_to='account_requests/%Y/%m/', null=True, blank=True)
    meter_documents = models.FileField("Документы на приборы учёта", upload_to='account_requests/%Y/%m/', null=True, blank=True)
    
    status = models.CharField("Статус заявки", max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    processed_at = models.DateTimeField("Дата обработки", null=True, blank=True)
    admin_comment = models.TextField("Комментарий администратора", blank=True)

    class Meta:
        verbose_name = "Заявка на открытие счета"
        verbose_name_plural = "Заявки на открытие счета"

    def __str__(self):
        return f"Заявка №{self.id} от {self.full_name} ({self.get_status_display()})"


class PersonalAccount(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='personal_accounts')
    account_number = models.CharField("Номер лицевого счёта", max_length=11, unique=True)
    balance = models.DecimalField("Текущий баланс (задолженность)", max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField("Активен", default=True)
    created_at = models.DateTimeField("Дата открытия", auto_now_add=True)
    address = models.CharField("Адрес помещения", max_length=300, blank=True)
    full_name = models.CharField("ФИО абонента", max_length=200, blank=True)

    class Meta:
        verbose_name = "Лицевой счёт"
        verbose_name_plural = "Лицевые счета"

    def __str__(self):
        return f"ЛС №{self.account_number} ({self.full_name})"

    @staticmethod
    def generate_account_number():
        while True:
            number = f"{random.randint(1000, 9999)}-{random.randint(100000, 999999)}"
            if not PersonalAccount.objects.filter(account_number=number).exists():
                return number
    
class LkMeterDevice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meters')
    account = models.ForeignKey(PersonalAccount, on_delete=models.CASCADE, related_name='meters', null=True, blank=True)
    device_number = models.CharField("Номер прибора", max_length=50)
    service_type = models.CharField(
        "Тип услуги",
        max_length=20,
        choices=SettingsTariff.SERVICE_CHOICES
    )
    verification_date = models.DateField("Дата поверки", null=True, blank=True)
    is_active = models.BooleanField("Активен", default=True)
    initial_reading = models.IntegerField("Начальные показания", default=0)

    class Meta:
        verbose_name = "Прибор учёта"
        verbose_name_plural = "Приборы учёта"
        ordering = ['user', 'service_type']
        db_table = 'lk_meter_device'

    def __str__(self):
        return f"{self.device_number} ({self.get_service_type_display()}) - {self.user.username}"

    def get_last_reading(self):
        return self.readings.order_by('-submitted_at').first()


class LkMeterReading(models.Model):
    device = models.ForeignKey(LkMeterDevice, on_delete=models.CASCADE, related_name='readings')
    tariff = models.ForeignKey(SettingsTariff, on_delete=models.PROTECT)
    submitted_at = models.DateTimeField("Дата подачи", auto_now_add=True)
    current_reading = models.IntegerField("Текущие показания")
    previous_reading = models.IntegerField("Предыдущие показания", editable=False)
    consumption = models.IntegerField("Расход (м³)", editable=False)
    amount_due = models.DecimalField("Сумма к оплате (руб)", max_digits=10, decimal_places=2, editable=False)

    class Meta:
        verbose_name = "Показание"
        verbose_name_plural = "Показания"
        ordering = ['-submitted_at']
        db_table = 'lk_meter_reading'

    def __str__(self):
        return f"{self.device.device_number}: {self.current_reading} от {self.submitted_at.date()}"

    def save(self, *args, **kwargs):
        if not self.pk:
            last = self.device.get_last_reading()
            self.previous_reading = last.current_reading if last else self.device.initial_reading
            self.consumption = max(0, self.current_reading - self.previous_reading)
            self.amount_due = self.consumption * self.tariff.price_per_unit
        super().save(*args, **kwargs)