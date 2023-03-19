from http import HTTPStatus

from django.test import TestCase


class ViewTestClass(TestCase):
    """Проверка страниц ошибок."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.address_and_template = [
            ['/nonexist-page/', 'core/404.html', HTTPStatus.NOT_FOUND],
        ]

    def test_error_page(self):
        for address, template, status in self.address_and_template:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, status)
            with self.subTest(address=address):
                self.assertTemplateUsed(response, template)
