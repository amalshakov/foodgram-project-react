from http import HTTPStatus

from django.test import Client, TestCase


class RecipeAPITestCase(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_list_recipes(self):
        """Проверка доступности списка задач."""
        response = self.guest_client.get('/api/recipes/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
