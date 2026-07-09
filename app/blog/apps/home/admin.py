from django.utils import timezone

from django.contrib import admin
from .models import (
    Menu, Slider, Client, Order, RequestUser,
    SettingsTariff, LkMeterDevice, LkMeterReading, SiteSettings, AccountRequest, PersonalAccount
)

admin.site.register(Menu)
admin.site.register(Slider)
admin.site.register(Client)
admin.site.register(Order)


class RequestUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'type_request', 'type_status', 'date')
    list_filter = ('type_request', 'type_status')
    search_fields = ('user__username', 'user__email')


admin.site.register(RequestUser, RequestUserAdmin)


@admin.register(SettingsTariff)
class SettingsTariffAdmin(admin.ModelAdmin):
    list_display = ('service_type', 'price_per_unit', 'valid_from', 'valid_until')
    list_filter = ('service_type',)
    search_fields = ('service_type',)


@admin.register(LkMeterDevice)
class LkMeterDeviceAdmin(admin.ModelAdmin):
    list_display = ('device_number', 'user', 'account', 'service_type', 'is_active', 'verification_date')
    list_filter = ('service_type', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('device_number', 'user__username', 'user__email', 'account__account_number')
    raw_id_fields = ('user', 'account')


@admin.register(LkMeterReading)
class LkMeterReadingAdmin(admin.ModelAdmin):
    list_display = ('device', 'submitted_at', 'current_reading', 'consumption', 'amount_due')
    list_filter = ('device__service_type', 'submitted_at')
    readonly_fields = ('previous_reading', 'consumption', 'amount_due')

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('reading_start_day', 'reading_end_day')

    def has_add_permission(self, request):
        # Запрещаем создавать больше одной записи
        return not SiteSettings.objects.exists()
    
@admin.register(AccountRequest)
class AccountRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'user', 'address', 'status', 'created_at', 'processed_at')
    list_filter = ('status', 'created_at')
    list_editable = ('status',)
    search_fields = ('full_name', 'address', 'user__email', 'user__username')
    readonly_fields = ('created_at',)
    actions = ['approve_requests']

    def approve_requests(self, request, queryset):
        total = queryset.count()
        pending = queryset.filter(status='pending').count()
        self.message_user(request, f"Выбрано заявок: {total}, из них со статусом 'pending': {pending}")
        # Дальше обычная логика
        for req in queryset.filter(status='pending'):
            client, created = Client.objects.get_or_create(
                client_mail=req.user.email,
                defaults={'client_name': req.full_name}
            )
            new_account = PersonalAccount.objects.create(
                client=client,
                account_number=PersonalAccount.generate_account_number(),
                address=req.address,
                full_name=req.full_name,
                is_active=True
            )
            req.status = 'approved'
            req.processed_at = timezone.now()
            req.save()
            self.message_user(
                request,
                f"Заявка №{req.id} одобрена. Создан лицевой счёт №{new_account.account_number} "
                f"для клиента {client.client_mail}."
            )
        self.message_user(request, f"Одобрено заявок: {queryset.filter(status='pending').count()}")

    approve_requests.short_description = "Одобрить выбранные заявки"


# --- Лицевые счета ---

@admin.register(PersonalAccount)
class PersonalAccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'full_name', 'address', 'balance', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('account_number', 'full_name', 'address')
    readonly_fields = ('account_number', 'created_at')
    actions = ['deactivate_accounts', 'activate_accounts']

    def deactivate_accounts(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Деактивировано счетов: {queryset.count()}")
    deactivate_accounts.short_description = "Деактивировать выбранные счета"

    def activate_accounts(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Активировано счетов: {queryset.count()}")
    activate_accounts.short_description = "Активировать выбранные счета"