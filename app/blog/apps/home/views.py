from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from users.forms import ProfileEditForm
from .forms import RequestUserForm, MeterDeviceForm, MeterReadingForm, PaymentForm, AccountRequestForm
from .models import (
    AccountRequest, Slider, Client, Order, RequestUser,
    LkMeterDevice, LkMeterReading,
    SettingsTariff, SiteSettings, PersonalAccount,
)
from django.contrib.auth.models import User


def index(request):
    """Главная страница со слайдером"""
    slides = Slider.objects.order_by('slider_queue')
    return render(request, "home/list.html", {
        'slides': slides,
        "first_slide": slides.first()
    })


def thank_you(request):
    """Страница благодарности после отправки срочной заявки"""
    return render(request, 'home/detail.html')


def send_hot_request(request):
    """Обработка срочной заявки с главной страницы"""
    client = Client()
    client.client_name = request.POST["name"]
    client.client_mail = request.POST["email"]
    client.save()

    Client.objects.get(id=client.id).order_set.create(
        order_object=request.POST["subject"],
        order_address=request.POST['address'],
        order_text=request.POST["message"]
    )

    request.session['email_from_hot_request'] = request.POST["email"]
    return HttpResponseRedirect(reverse('home:thank_you'))


@login_required
def account(request):
    user = request.user
    client, _ = Client.objects.get_or_create(
        client_mail=user.email,
        defaults={'client_name': user.username}
    )

    settings = SiteSettings.load()
    is_reading_period = settings.is_reading_allowed()

    # --- Все активные счета клиента ---
    active_accounts = PersonalAccount.objects.filter(client=client, is_active=True).order_by('-created_at')
    has_account = active_accounts.exists()

    # --- Определяем выбранный счёт ---
    selected_account_id = request.GET.get('account_id')
    personal_account = None
    if selected_account_id:
        personal_account = active_accounts.filter(id=selected_account_id).first()
    if not personal_account:
        personal_account = active_accounts.first() if has_account else None

    pending_request = AccountRequest.objects.filter(user=user, status='pending').first()

    active_tab = request.GET.get('tab', '3')
    if active_tab not in ['1', '2', '3', '4', '5']:
        active_tab = '3'

    if not has_account and active_tab in ['1', '2', '5']:
        active_tab = '4'
        messages.info(request, "Для работы с заявками и приборами учёта необходим лицевой счёт.")

    # --- 1. Профиль ---
    if request.method == 'POST' and 'edit_profile' in request.POST:
        profile_form = ProfileEditForm(request.POST, instance=user)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Данные профиля обновлены.")
            return redirect(f"{reverse('home:account')}?tab=3")
    else:
        profile_form = ProfileEditForm(instance=user)

    # --- 2. Добавление прибора ---
    if request.method == 'POST' and 'add_meter' in request.POST:
        if not has_account:
            messages.error(request, "Сначала откройте лицевой счёт.")
            return redirect(f"{reverse('home:account')}?tab=4")
        meter_form = MeterDeviceForm(request.POST, active_accounts=active_accounts)
        if meter_form.is_valid():
            meter = meter_form.save(commit=False)
            meter.user = user
            # account уже установлен формой, но на всякий случай можно не дублировать
            meter.save()
            messages.success(request, "Прибор учёта добавлен.")
            return redirect(f"{reverse('home:account')}?tab=5")
    else:
        meter_form = MeterDeviceForm(active_accounts=active_accounts)

    # --- 3. Заявка на открытие счёта ---
    if request.method == 'POST' and 'submit_account_request' in request.POST:
        request_form_account = AccountRequestForm(request.POST, request.FILES)
        if request_form_account.is_valid():
            account_req = request_form_account.save(commit=False)
            account_req.user = user
            account_req.save()
            messages.success(request, "Заявка на открытие лицевого счета отправлена.")
            return redirect(f"{reverse('home:account')}?tab=4")
    else:
        initial_account = {}
        if hasattr(user, 'profile'):
            initial_account['full_name'] = user.profile.full_name
            initial_account['phone'] = user.profile.phone_number
        request_form_account = AccountRequestForm(initial=initial_account)

    # --- 4. Оплата (привязана к выбранному счёту) ---
    if request.method == 'POST' and 'make_payment' in request.POST:
        if not personal_account:
            messages.error(request, "Выберите лицевой счёт.")
            return redirect(f"{reverse('home:account')}?tab=4")
        payment_form = PaymentForm(request.POST)
        if payment_form.is_valid():
            amount = payment_form.cleaned_data['amount']
            personal_account.balance -= amount
            personal_account.save()
            messages.success(request, f"Оплата на сумму {amount} руб. выполнена.")
            return redirect(f"{reverse('home:account')}?tab=4&account_id={personal_account.id}")
    else:
        payment_form = PaymentForm()

    # --- Сбор данных для вкладок (только если есть счёт) ---
    meters_with_status = []
    readings = []
    if has_account and personal_account:
        # Приборы, привязанные к любому из активных счетов
        meters = LkMeterDevice.objects.filter(user=user, account__in=active_accounts, is_active=True)
        today = timezone.now().date()
        period_start = today.replace(day=settings.reading_start_day)
        if today.day < settings.reading_start_day:
            period_start = (period_start - timezone.timedelta(days=28)).replace(day=settings.reading_start_day)

        for meter in meters:
            has_submitted = meter.readings.filter(submitted_at__date__gte=period_start).exists()
            can_submit = is_reading_period and (settings.allow_multiple_readings or not has_submitted)
            meters_with_status.append({
                'meter': meter,
                'has_submitted': has_submitted,
                'can_submit': can_submit,
            })

        # Последние начисления для выбранного счёта
        readings = LkMeterReading.objects.filter(
            device__account=personal_account
        ).select_related('device', 'tariff').order_by('-submitted_at')[:10]

    request_form = RequestUserForm()
    data = client.get_full_info()

    context = {
        'form': request_form,
        'profile_form': profile_form,
        'meter_form': meter_form,
        'meters_with_status': meters_with_status,
        'data': data,
        'active_tab': active_tab,
        'is_reading_period': is_reading_period,
        'site_settings': settings,
        'active_accounts': active_accounts,
        'personal_account': personal_account,
        'has_account': has_account,
        'selected_account_id': personal_account.id if personal_account else None,
        'pending_request': pending_request,
        'account_request_form': request_form_account,
        'payment_form': payment_form,
        'readings': readings,
    }
    return render(request, 'home/account.html', context)


@login_required
def send_request(request):
    """Отправка заявки (технические условия / договор)"""
    request_user = RequestUser(
        user=User.objects.get(id=request.user.id),
        request_file=request.FILES['request_file'],
        request_message=request.POST['request_message'],
        type_request=request.POST['type_request'],
    )
    request_user.save()
    return HttpResponseRedirect(reverse("home:account"))


@login_required
def deactivate_meter(request, meter_id):
    """Деактивация прибора учёта пользователем"""
    meter = get_object_or_404(LkMeterDevice, id=meter_id, user=request.user)
    meter.is_active = False
    meter.save()
    return redirect(f"{reverse('home:account')}?tab=5")


@login_required
def submit_reading(request, meter_id):
    """Подача показаний по прибору учёта"""
    meter = get_object_or_404(LkMeterDevice, id=meter_id, user=request.user, is_active=True)

    # Проверка разрешённого периода
    settings = SiteSettings.load()
    if not settings.is_reading_allowed():
        messages.warning(
            request,
            f"Подача показаний разрешена только с {settings.reading_start_day} "
            f"по {settings.reading_end_day} число каждого месяца."
        )
        return redirect(f"{reverse('home:account')}?tab=5")

    # Проверка наличия активного лицевого счёта у прибора
    if not meter.account or not meter.account.is_active:
        messages.error(request, "У прибора отсутствует активный лицевой счёт.")
        return redirect(f"{reverse('home:account')}?tab=5")

    if request.method == 'POST':
        form = MeterReadingForm(request.POST)
        if form.is_valid():
            new_reading = form.cleaned_data['current_reading']
            last_reading = meter.get_last_reading()
            prev_value = last_reading.current_reading if last_reading else meter.initial_reading

            if new_reading < prev_value:
                messages.error(request, f"Показание не может быть меньше предыдущего ({prev_value}).")
                return redirect(f"{reverse('home:account')}?tab=5")

            # Получаем действующий тариф
            tariff = SettingsTariff.objects.filter(
                service_type=meter.service_type,
                valid_from__lte=timezone.now().date()
            ).order_by('-valid_from').first()

            if not tariff:
                messages.error(request, "Не найден действующий тариф для этой услуги.")
                return redirect(f"{reverse('home:account')}?tab=5")

            # Создаём показание (расход и сумма рассчитаются в save())
            reading = LkMeterReading(
                device=meter,
                tariff=tariff,
                current_reading=new_reading
            )
            reading.save()

            # Обновляем баланс лицевого счёта (увеличиваем задолженность)
            personal_account = meter.account   # теперь напрямую берём связанный счёт
            personal_account.balance += reading.amount_due
            personal_account.save()

            messages.success(request, "Показания успешно переданы.")
        else:
            messages.error(request, "Некорректное значение показания.")
    return redirect(f"{reverse('home:account')}?tab=5")


@login_required
def meter_history(request, meter_id):
    """История показаний конкретного прибора"""
    meter = get_object_or_404(LkMeterDevice, id=meter_id, user=request.user)
    readings = meter.readings.order_by('-submitted_at')
    return render(request, 'home/meter_history.html', {
        'meter': meter,
        'readings': readings,
    })