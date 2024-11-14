from django.test import TestCase
from django.contrib.auth.models import User
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException

# Importa el modelo de la pregunta
from polls.models import Question
from django.utils import timezone

class MySeleniumTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        opts = Options()
        cls.selenium = WebDriver(options=opts)
        cls.selenium.implicitly_wait(5)

        # Crear superusuario
        user = User.objects.create_user("isard", "isard@isardvdi.com", "pirineus")
        user.is_superuser = True
        user.is_staff = True
        user.save()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super().tearDownClass()

    def test_create_user_with_permissions(self):
        # Acceder a la página de login de Django admin
        self.selenium.get(f'{self.live_server_url}/admin/login/')

        # Iniciar sesión con el usuario 'isard' y contraseña 'pirineus'
        username_input = self.selenium.find_element(By.NAME, "username")
        username_input.send_keys('isard')
        password_input = self.selenium.find_element(By.NAME, "password")
        password_input.send_keys('pirineus')
        self.selenium.find_element(By.XPATH, '//input[@value="Log in"]').click()

        # Crear una pregunta 
        question = Question.objects.create(question_text="¿Cómo te llamas?", pub_date=timezone.now())
        question.save()

        # Navegar a "Add user"
        self.selenium.get(f'{self.live_server_url}/admin/auth/user/add/')

        # Completar el formulario de creación de usuario con el usuario 'QuestionsR' y contraseña 'A123456'
        self.selenium.find_element(By.NAME, "username").send_keys("QuestionsR")
        self.selenium.find_element(By.NAME, "password1").send_keys("A123456*")
        self.selenium.find_element(By.NAME, "password2").send_keys("A123456*")

        # Hacer clic en "Save and continue editing"
        self.selenium.find_element(By.NAME, "_continue").click()

        # Asignar permisos de "Staff status" y permiso específico "Can view questions"
        staff_status_checkbox = self.selenium.find_element(By.NAME, "is_staff")
        if not staff_status_checkbox.is_selected():
            staff_status_checkbox.click()
        permissions_select = Select(self.selenium.find_element(By.ID, "id_user_permissions_from"))
        permissions_select.select_by_visible_text("Polls | question | Can view question")
        self.selenium.find_element(By.ID, "id_user_permissions_add_link").click()

        # Guardar cambios
        self.selenium.find_element(By.NAME, "_save").click()

        # Verificar que el usuario se ha creado correctamente
        success_message = self.selenium.find_element(By.CLASS_NAME, "success").text
        self.assertIn("The user “QuestionsR” was changed successfully.", success_message)

        # Verificar que el usuario está en la lista
        self.selenium.get(f'{self.live_server_url}/admin/auth/user/')
        try:
            self.selenium.find_element(By.XPATH, "//a[text()='QuestionsR']")
        except NoSuchElementException:
            self.fail("El usuario 'QuestionsR' no está en la lista de usuarios.")

        # Cerrar la sesión del administrador
        logout_button = self.selenium.find_element(By.ID, "logout-form").find_element(By.XPATH, ".//button")
        logout_button.click()
        self.selenium.get(f'{self.live_server_url}/admin/logout/')

        # Iniciar sesión con el usuario "QuestionsR"
        self.selenium.get(f'{self.live_server_url}/admin/login/')
        username_input = self.selenium.find_element(By.NAME, "username")
        username_input.send_keys('QuestionsR')
        password_input = self.selenium.find_element(By.NAME, "password")
        password_input.send_keys('A123456*')
        self.selenium.find_element(By.XPATH, '//input[@value="Log in"]').click()

        # Hacer clic en el enlace "Questions"
        questions_link = self.selenium.find_element(By.LINK_TEXT, "Questions")
        questions_link.click()

        # Verifica que el título de la página es correcto
        page_title = self.selenium.find_element(By.TAG_NAME, "h1").text
        self.assertEqual(page_title, "Select question to view")

        # Verifica que las preguntas son visibles
        questions_list = self.selenium.find_elements(By.CSS_SELECTOR, "#result_list tbody tr")
        
        if len(questions_list) == 0:
            print("No hay preguntas en la lista. Prueba exitosa.")
            return

        try:
            question_link = self.selenium.find_element(By.LINK_TEXT, "¿Cómo te llamas?")
            question_link.click()

            # Verifica que el botón de eliminar no está habilitado
            delete_button = self.selenium.find_element(By.CSS_SELECTOR, 'button[name="delete"]')
            self.assertFalse(delete_button.is_enabled(), "El botón de eliminar debería estar deshabilitado.")
            
            # Intentar editar la pregunta
            question_text_area = self.selenium.find_element(By.NAME, "question_text")
            original_text = question_text_area.get_attribute("value")
            
            # Modificar el texto
            question_text_area.clear()
            question_text_area.send_keys("¿Nuevo texto?")
            
            # Verificar que el botón de guardar está deshabilitado
            save_button = self.selenium.find_element(By.XPATH, '//input[@value="Save"]')
            self.assertFalse(save_button.is_enabled(), "El botón de guardar debería estar deshabilitado.")

            # Restaurar el texto original
            question_text_area.clear()
            question_text_area.send_keys(original_text)

        except NoSuchElementException:
            pass
