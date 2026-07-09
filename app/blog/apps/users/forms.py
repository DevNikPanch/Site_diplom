import unicodedata

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import Profile


class UsernameField(forms.CharField):
    def to_python(self, value):
        return unicodedata.normalize("NFKC", super().to_python(value))

    def widget_attrs(self, widget):
        return {
            **super().widget_attrs(widget),
            "autocapitalize": "none",
            "autocomplete": "username",
        }


class UserCreationFormCustom(forms.ModelForm):
    error_messages = {
        "password_mismatch": _("Не заполнены поля с паролями."),
    }
    password1 = forms.CharField(
        label=_("Пароль"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_("Подтверждение пароля"),
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        strip=False,
        help_text=_("Введите пароль повторно для подтверждения."),
    )
    email = forms.EmailField(
        label=_("Почта"),
        help_text=_("Если вы заполняли форму на главной, то впишите её же сюда"),
    )
    full_name = forms.CharField(
        label="ФИО",
        max_length=200,
        required=True,
        help_text="Введите ваши полные фамилию, имя и отчество"
    )
    phone_number = forms.CharField(
        label="Номер телефона",
        max_length=20,
        required=True,
        help_text="Введите контактный номер телефона"
    )

    class Meta:
        model = User
        fields = ("username", "email")
        field_classes = {"username": UsernameField}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._meta.model.USERNAME_FIELD in self.fields:
            self.fields[self._meta.model.USERNAME_FIELD].widget.attrs["autofocus"] = True

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not email:
            raise ValidationError(_("Пожалуйста, укажите email."))
        email = email.lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(_("Пользователь с такой почтой уже существует."))
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages["password_mismatch"],
                code="password_mismatch",
            )
        return password2

    def _post_clean(self):
        super()._post_clean()
        password = self.cleaned_data.get("password2")
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error("password2", error)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            profile, created = Profile.objects.get_or_create(user=user)
            profile.full_name = self.cleaned_data.get('full_name', '')
            profile.phone_number = self.cleaned_data.get('phone_number', '')
            profile.email = self.cleaned_data.get('email', '')
            profile.save()
        return user


class ProfileEditForm(forms.ModelForm):
    email = forms.EmailField(label='Email')

    full_name = forms.CharField(label='ФИО', max_length=200, required=False)
    phone_number = forms.CharField(label='Номер телефона', max_length=20, required=False)

    class Meta:
        model = User
        fields = []

    def __init__(self, *args, **kwargs):
        self.instance_user = kwargs.pop('instance_user', None) or kwargs.get('instance')
        super().__init__(*args, **kwargs)
        if self.instance_user:
            self.fields['email'].initial = self.instance_user.email
            profile = getattr(self.instance_user, 'profile', None)
            if profile:
                self.fields['full_name'].initial = profile.full_name
                self.fields['phone_number'].initial = profile.phone_number

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.exclude(pk=self.instance_user.pk).filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email

    def save(self, commit=True):
        user = self.instance_user
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.full_name = self.cleaned_data.get('full_name', '')
            profile.phone_number = self.cleaned_data.get('phone_number', '')
            profile.email = user.email
            profile.save()
        return user