from django import forms
from .const import TYPE_REQUEST_USER
from .models import LkMeterReading, PersonalAccount, RequestUser, LkMeterDevice, AccountRequest


class RequestUserForm(forms.ModelForm):
    type_request = forms.ChoiceField(
        choices=TYPE_REQUEST_USER,
        widget=forms.RadioSelect(attrs={'class': 'form__radio'}),
        initial='1',
        label='Тип заявки'
    )
    request_file = forms.FileField(label='Файл заявления')
    request_message = forms.CharField(
        label='Сообщение',
        widget=forms.Textarea(attrs={'rows': 6, 'cols': 25})
    )

    class Meta:
        model = RequestUser
        fields = ['type_request', 'request_file', 'request_message']


class MeterDeviceForm(forms.ModelForm):
    class Meta:
        model = LkMeterDevice
        fields = ['device_number', 'service_type', 'verification_date', 'initial_reading', 'account']
        widgets = {
            'verification_date': forms.DateInput(attrs={'type': 'date'}),
            'account': forms.Select(),  # выпадающий список
        }
        labels = {
            'device_number': 'Номер прибора',
            'service_type': 'Тип услуги',
            'verification_date': 'Дата поверки',
            'initial_reading': 'Начальные показания',
            'account': 'Привязать к лицевому счёту',
        }

    def __init__(self, *args, **kwargs):
        # Принимаем список активных счетов из представления
        active_accounts = kwargs.pop('active_accounts', PersonalAccount.objects.none())
        super().__init__(*args, **kwargs)
        if active_accounts:
            self.fields['account'].queryset = active_accounts
            self.fields['account'].required = True
        else:
            self.fields['account'].widget = forms.HiddenInput()
            self.fields['account'].required = False

class MeterReadingForm(forms.ModelForm):
    class Meta:
        model = LkMeterReading
        fields = ['current_reading']
        labels = {'current_reading': 'Текущее показание'}
        widgets = {
            'current_reading': forms.NumberInput(attrs={'min': 0, 'step': 1, 'required': True})
        }

class PaymentForm(forms.Form):
    amount = forms.DecimalField(
        label="Сумма оплаты (руб.)",
        max_digits=10,
        decimal_places=2,
        min_value=0.01,
        widget=forms.NumberInput(attrs={'step': '0.01', 'placeholder': 'Введите сумму'})
    )

class AccountRequestForm(forms.ModelForm):
    class Meta:
        model = AccountRequest
        fields = [
            'applicant_type', 'full_name', 'phone', 'address',
            'ownership_document', 'passport_copy', 'snils_copy', 'meter_documents',
            'company_name', 'inn', 'kpp', 'manager_position'
        ]
        labels = {
            'applicant_type': 'Тип заявителя',
            'full_name': 'ФИО заявителя',
            'phone': 'Контактный телефон',
            'address': 'Адрес помещения (как в ЕГРН)',
            'ownership_document': 'Правоустанавливающий документ',
            'passport_copy': 'Копия паспорта',
            'snils_copy': 'Копия СНИЛС (при наличии)',
            'meter_documents': 'Документы на приборы учёта',
            'company_name': 'Наименование организации',
            'inn': 'ИНН',
            'kpp': 'КПП',
            'manager_position': 'Должность руководителя',
        }
        widgets = {
            'applicant_type': forms.RadioSelect(attrs={'class': 'applicant-type-radio'}),
            'address': forms.TextInput(attrs={'placeholder': 'г. Ульяновск, ул. Примерная, д. 1'}),
            'phone': forms.TextInput(attrs={'placeholder': '+7 (XXX) XXX-XX-XX'}),
        }