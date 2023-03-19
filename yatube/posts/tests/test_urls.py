from http import HTTPStatus

from django.test import TestCase, Client
from django.core.cache import cache

from posts.models import Post, Group, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=User.objects.create_user(username='Foo', password='barbaz'),
            group=Group.objects.create(title='TestGroup', slug='test_slug')
        )
        cls.case_for_authorized_client = {
            '/create/': HTTPStatus.OK,
            f'/posts/{cls.post.id}/edit/?': HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            f'/profile/{cls.post.author}/follow/': HTTPStatus.FOUND,
            f'/profile/{cls.post.author}/unfollow/': HTTPStatus.FOUND,
        }
        cls.case_for_guest_client = {
            '/': HTTPStatus.OK,
            f'/group/{cls.post.group.slug}/': HTTPStatus.OK,
            f'/profile/{cls.post.author.username}/': HTTPStatus.OK,
            f'/posts/{cls.post.id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
            f'/posts/{cls.post.id}/comment/': HTTPStatus.FOUND,
            f'/profile/{cls.post.author}/unfollow/': HTTPStatus.FOUND,
        }
        cls.adress_and_template = {
            '/': 'posts/index.html',
            f'/group/{cls.post.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.post.author.username}/': 'posts/profile.html',
            f'/posts/{cls.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post.id}/edit/?': 'posts/create_post.html',
        }
        cls.case_for_redirects_guest = {
            '/create/': '/auth/login/?next=/create/',
            f'/posts/{cls.post.id}/edit/?':
            f'/auth/login/?next=/posts/{cls.post.id}/edit/',
            f'/posts/{cls.post.id}/comment/':
            f'/auth/login/?next=/posts/{cls.post.id}/comment/',
            f'/profile/{cls.post.author}/follow/':
            f'/auth/login/?next=/profile/{cls.post.author}/follow/',
        }

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.post.author)

    def test_urls_uses_correct_template(self):
        """Проверка корректности выбора шаблонов."""
        for address, template in self.adress_and_template.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_correct_urls_location_with_authotized_client(self):
        """
        Проверка доступности адресов для авторизованного пользователя.
        """
        for address, status_code in self.case_for_authorized_client.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, status_code)
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/?')
        self.assertRedirects(
            response, f'/posts/{self.post.id}/'
        )

    def test_correct_urls_location_with_guest_client(self):
        """
        Проверка доступности адресов для не авторизованного пользователя.
        """
        for address, status_code in self.case_for_guest_client.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status_code)
        for address, add_address in self.case_for_redirects_guest.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertRedirects(response, add_address)
