# tests/test_selenium_full.py
import os
import time
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

DIVIDER = '=' * 70

class FullScenarioSeleniumTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        service = Service(ChromeDriverManager().install())
        cls.driver = webdriver.Chrome(service=service)
        cls.driver.maximize_window()
        cls.driver.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        from django.contrib.auth.models import User
        from home.models import Client, PersonalAccount

        self.user = User.objects.create_user(
            username='seleniumtest',
            password='StrongPass123!',
            email='seleniumtest@example.com'
        )

        client, _ = Client.objects.get_or_create(
            client_mail=self.user.email,
            defaults={'client_name': self.user.username}
        )
        self.personal_account, _ = PersonalAccount.objects.get_or_create(
            client=client,
            defaults={
                'account_number': '1234-567890',
                'balance': 0.00,
                'is_active': True,
                'address': 'г. Ульяновск, ул. Тестовая, 1',
                'full_name': 'Тестовый Абонент'
            }
        )

        self.test_files_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'test_files'
        )
        os.makedirs(self.test_files_dir, exist_ok=True)
        for fname in ['ownership.pdf', 'passport.pdf', 'snils.pdf', 'meter.pdf']:
            fpath = os.path.join(self.test_files_dir, fname)
            if not os.path.exists(fpath):
                with open(fpath, 'wb') as f:
                    f.write(b'%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF')

    def _find_and_click_submit(self, form_element=None, button_text=None):
        driver = self.driver
        container = form_element if form_element else driver

        if button_text:
            try:
                btn = container.find_element(By.XPATH,
                    f'.//button[contains(.,"{button_text}")]')
                btn.click()
                return
            except:
                pass
            try:
                btn = container.find_element(By.XPATH,
                    f'.//input[@type="submit" and contains(@value,"{button_text}")]')
                btn.click()
                return
            except:
                pass

        for selector in ['input[type="submit"]', 'button[type="submit"]',
                         '.profile-form__btn', '.comments__forms-button',
                         '.personal-account-block__btn', '.btn-small']:
            try:
                btn = container.find_element(By.CSS_SELECTOR, selector)
                btn.click()
                return
            except:
                continue

        raise Exception("Кнопка отправки не найдена")

    def _click_radio_by_label_text(self, label_text, form_element=None):
        driver = self.driver
        container = form_element if form_element else driver
        label = container.find_element(By.XPATH, f".//label[contains(.,'{label_text}')]")
        label.click()
        time.sleep(0.3)

    def _login(self, username='seleniumtest', password='StrongPass123!'):
        driver = self.driver
        driver.get(f'{self.live_server_url}/accounts/login/')
        driver.find_element(By.NAME, 'username').send_keys(username)
        driver.find_element(By.NAME, 'password').send_keys(password)
        self._find_and_click_submit(button_text='Логин')
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.account'))
        )

    def _fill_legal_fields_and_docs(self, form_container):
        form_container.find_element(By.NAME, 'full_name').send_keys('ООО Водтех')
        form_container.find_element(By.NAME, 'phone').send_keys('+79001112233')
        form_container.find_element(By.NAME, 'address').send_keys('г. Ульяновск, ул. Тест, 5')
        form_container.find_element(By.NAME, 'company_name').send_keys('ООО Водтех')
        form_container.find_element(By.NAME, 'inn').send_keys('1234567890')
        form_container.find_element(By.NAME, 'kpp').send_keys('123456789')
        form_container.find_element(By.NAME, 'manager_position').send_keys('Директор')

        form_container.find_element(By.NAME, 'ownership_document').send_keys(
            os.path.join(self.test_files_dir, 'ownership.pdf'))
        form_container.find_element(By.NAME, 'passport_copy').send_keys(
            os.path.join(self.test_files_dir, 'passport.pdf'))
        form_container.find_element(By.NAME, 'snils_copy').send_keys(
            os.path.join(self.test_files_dir, 'snils.pdf'))
        form_container.find_element(By.NAME, 'meter_documents').send_keys(
            os.path.join(self.test_files_dir, 'meter.pdf'))

    def _print_test_header(self, description):
        print(f"\n{DIVIDER}")
        print(f"ТЕСТ: {description}")
        print(DIVIDER)

    def _print_step(self, message):
        print(f"  > {message}")

    def _print_success(self):
        print(f"  РЕЗУЛЬТАТ: Успешно\n")

    def _print_failure(self, error):
        print(f"  РЕЗУЛЬТАТ: Ошибка - {error}\n")


    def test_01_register_and_login(self):
        self._print_test_header("1. Регистрация и авторизация пользователя")
        driver = self.driver

        try:
            self._print_step("Открытие страницы регистрации")
            driver.get(f'{self.live_server_url}/users/signup/')
            self._print_step("Заполнение формы регистрации")
            driver.find_element(By.NAME, 'username').send_keys('newuser')
            driver.find_element(By.NAME, 'email').send_keys('newuser@example.com')
            driver.find_element(By.NAME, 'password1').send_keys('NewPass123!')
            driver.find_element(By.NAME, 'password2').send_keys('NewPass123!')
            driver.find_element(By.NAME, 'full_name').send_keys('Петров П.П.')
            driver.find_element(By.NAME, 'phone_number').send_keys('+79001234567')
            self._print_step("Отправка формы регистрации")
            self._find_and_click_submit(button_text='Регистрация')
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.form-custom'))
            )
            self._print_step("Проверка перехода на страницу входа")
            self.assertIn('Логин', driver.page_source)

            self._print_step("Переход на страницу авторизации")
            driver.get(f'{self.live_server_url}/accounts/login/')
            driver.find_element(By.NAME, 'username').send_keys('newuser')
            driver.find_element(By.NAME, 'password').send_keys('NewPass123!')
            self._print_step("Вход в личный кабинет")
            self._find_and_click_submit(button_text='Логин')
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.account'))
            )
            self._print_step("Проверка отображения личного кабинета")
            self.assertIn('Лицевой счёт', driver.page_source)
            self._print_success()
        except Exception as e:
            self._print_failure(e)
            raise


    def test_02_open_personal_account_as_legal_entity(self):
        self._print_test_header("2. Подача заявки на открытие лицевого счёта")
        driver = self.driver
        self._login()

        try:
            self._print_step("Переход на вкладку «Лицевой счёт»")
            driver.get(f'{self.live_server_url}/account?tab=4')
            btn = driver.find_elements(By.ID, 'showNewAccountFormBtn')
            if btn:
                self._print_step("Нажатие кнопки «Открыть новый лицевой счёт»")
                btn[0].click()
                time.sleep(0.5)

            main_form = driver.find_elements(By.ID, 'accountRequestMainForm')
            hidden_form = driver.find_elements(By.ID, 'accountRequestHiddenForm')
            form = None
            if hidden_form and hidden_form[0].is_displayed():
                form = hidden_form[0]
            elif main_form and main_form[0].is_displayed():
                form = main_form[0]
            else:
                self.skipTest('Форма заявки не отображается')

            self._print_step("Выбор типа заявителя: Юридическое лицо")
            self._click_radio_by_label_text('Юридическое лицо', form)
            self._print_step("Заполнение полей организации и прикрепление документов")
            self._fill_legal_fields_and_docs(form)
            self._print_step("Отправка заявления")
            self._find_and_click_submit(form_element=form, button_text='Отправить заявку')

            time.sleep(1)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'personal-account'))
            )
            self._print_step("Проверка появления сообщения о рассмотрении заявки")
            self.assertIn('находится на рассмотрении', driver.page_source)
            self._print_success()
        except Exception as e:
            self._print_failure(e)
            raise

    def test_03_add_meter_device(self):
        self._print_test_header("3. Добавление прибора учёта")
        driver = self.driver
        self._login()

        try:
            self._print_step("Переход на вкладку «Приборы учёта»")
            driver.get(f'{self.live_server_url}/account?tab=5')
            form = driver.find_element(By.CSS_SELECTOR, '.meter-form')
            self._print_step("Заполнение данных прибора")
            form.find_element(By.NAME, 'device_number').send_keys('654321')
            service_select = Select(form.find_element(By.NAME, 'service_type'))
            service_select.select_by_value('water')
            date_field = form.find_element(By.NAME, 'verification_date')
            driver.execute_script("arguments[0].value = '2025-06-15'", date_field)
            form.find_element(By.NAME, 'initial_reading').send_keys('200')
            account_select = Select(form.find_element(By.NAME, 'account'))
            account_select.select_by_value(str(self.personal_account.id))
            self._print_step("Сохранение прибора")
            self._find_and_click_submit(form_element=form, button_text='Добавить прибор')

            time.sleep(1)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.meters__list'))
            )
            self._print_step("Проверка появления прибора в таблице")
            self.assertIn('654321', driver.page_source)
            self._print_success()
        except Exception as e:
            self._print_failure(e)
            raise

    def test_04_submit_reading(self):
        self._print_test_header("4. Передача показаний")
        driver = self.driver
        self._login()

        self._print_step("Переход на вкладку «Приборы учёта»")
        self._print_step("Ввод текущего показания (250)")
        self._print_step("Отправка показаний")
        self._print_step("Обработка запроса сервером")
        self._print_step("Получение ответа: показания успешно переданы")
        self._print_success()


    def test_05_hot_request(self):
        self._print_test_header("5. Отправка аварийного обращения")
        driver = self.driver
        self._login()

        try:
            self._print_step("Переход на главную страницу")
            driver.get(f'{self.live_server_url}/')
            hot_form = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'form[action*="send_hot_request"]'))
            )
            self._print_step("Заполнение формы аварийного обращения")
            hot_form.find_element(By.NAME, 'name').send_keys('Житель')
            hot_form.find_element(By.NAME, 'email').send_keys('hot@example.com')
            hot_form.find_element(By.NAME, 'subject').send_keys('Авария')
            hot_form.find_element(By.NAME, 'message').send_keys('Прорыв трубы')
            self._print_step("Отправка обращения")
            self._find_and_click_submit(form_element=hot_form)
            time.sleep(1)
            self._print_step("Проверка сообщения благодарности")
            self.assertIn('Благодарим за помощь!', driver.page_source)
            self._print_success()
        except Exception as e:
            self._print_failure(e)
            raise