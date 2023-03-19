import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache

from ..models import Comment, Follow, Group, Post, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=User.objects.create_user(username='Foo', password='barbaz'),
            group=Group.objects.create(title='TestGroup', slug='test_slug'),
            image=uploaded,
        )
        cls.test_group2 = Group.objects.create(
            title='TestGroup2', slug='test_slug2'
        )
        cls.comment = Comment.objects.create(
            text='Тестовый коммент',
            post=cls.post,
            author=cls.post.author,
        )
        cls.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_posts', args={cls.post.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', args={cls.post.author.username}):
            'posts/profile.html',
            reverse('posts:post_detail', args={cls.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', args={cls.post.id}):
            'posts/create_post.html',
        }
        cls.fields_form = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
            'image': forms.fields.ImageField,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.client.force_login(self.post.author)
        self.user = User.objects.create_user(username='StasBasov')
        self.author2 = Client()
        self.author2.force_login(self.user)

    def tearDown(self):
        Follow.objects.all().delete()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:post_detail', args={self.post.id}))
        first_post = {
            response.context['post'].text: self.post.text,
            response.context['post'].group: self.post.group,
            response.context['post'].author: self.post.author.username,
            response.context['post'].image: self.post.image,
            response.context['comments'].text: self.comment.text,
            response.context['comments'].author: self.comment.author,
        }
        for value, expected in first_post.items():
            with self.subTest(value=value):
                self.assertEqual(first_post[value], expected)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:group_posts', args={self.post.group.slug}))
        first_post = {
            response.context['group'].title: self.post.group.title,
            response.context['group'].slug: self.post.group.slug,
            response.context['page_obj'].object_list[0].image: self.post.image,
        }
        for value, expected in first_post.items():
            with self.subTest(value=value):
                self.assertEqual(first_post[value], expected)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:index'))
        first_post = {
            response.context['page_obj'].object_list[0].text: self.post.text,
            response.context['page_obj'].object_list[0].group: self.post.group,
            response.context['page_obj'].object_list[0].image: self.post.image,
        }
        for value, expected in first_post.items():
            with self.subTest(value=value):
                self.assertEqual(first_post[value], expected)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:profile', args={self.post.author.username}))
        first_post = {
            response.context['author'].username: self.post.author.username,
            response.context['author'].password: self.post.author.password,
            response.context['page_obj'].object_list[0].image: self.post.image,
        }
        for value, expected in first_post.items():
            with self.subTest(value=value):
                self.assertEqual(first_post[value], expected)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.client.get(reverse('posts:post_create'))
        for value, expected in self.fields_form.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.client.get(reverse('posts:post_edit',
                                           args={self.post.id}))
        for value, expected in self.fields_form.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        # И в поля формы подтянулся нужный пост.
        self.assertEqual(response.context.get('form').instance, self.post)

    def test_location_of_the_new_post_is_correct(self):
        """
        Новый пост с указанной при создании группой появляется
        в нужных разделах.
        """
        response_index = self.client.get(
            reverse('posts:index')
        )
        response_group = self.client.get(
            reverse('posts:group_posts', args={self.post.group.slug})
        )
        response_profile = self.client.get(
            reverse('posts:profile', args={self.post.author.username})
        )
        objects_in_index = response_index.context['page_obj']
        objects_in_group = response_group.context['page_obj']
        objects_in_profile = response_profile.context['page_obj']
        self.assertIn(self.post, objects_in_index)
        self.assertIn(self.post, objects_in_group)
        self.assertIn(self.post, objects_in_profile)

    def test_new_post_did_not_appear_in_another_group(self):
        """Новый пост не появился в групповом листе другой группы."""
        new_post = Post.objects.create(text='Новый пост',
                                       author=self.user,
                                       group=self.post.group)
        response = self.client.get(
            reverse('posts:group_posts', args={self.test_group2.slug})
        )
        objects_in_test_group2 = response.context['page_obj']
        self.assertNotIn(new_post, objects_in_test_group2)

    def test_cache_index_page(self):
        """Проверка кэширования главной страницы."""
        new_post = Post.objects.create(
            text='New text',
            author=self.user,
        )
        response = self.client.get(reverse('posts:index'))
        new_post.delete()
        response_in_cache = self.client.get(reverse('posts:index'))
        self.assertEqual(response.content, response_in_cache.content)
        cache.clear()
        response_not_in_cache = self.client.get(reverse('posts:index'))
        self.assertNotEqual(
            response_in_cache.content, response_not_in_cache.content
        )

    def test_follow_and_unfollow_authorized_user(self):
        """
        Авторизованный пользователь может подписываться на
        других пользователей и удалять их из подписок.
        """
        self.assertFalse(Follow.objects.filter(        # До этого теста
            user=self.user, author=self.post.author))  # подписок не было
        self.author2.get(reverse(
            'posts:profile_follow', args={self.post.author.username}
        ))
        self.assertEqual(Follow.objects.filter(
            user=self.user, author=self.post.author).count(), 1)
        self.author2.get(reverse(
            'posts:profile_unfollow', args={self.post.author.username}
        ))
        self.assertFalse(Follow.objects.filter(
            user=self.user, author=self.post.author))

    def test_visibility_following_new_post(self):
        """
        Запись пользователя появляется в ленте тех, кто на него
        подписан и не появляется в ленте тех,кто не подписан.
        """
        # Добавила удаление всех объектов Follow в tearDown.
        response_non_follower = self.author2.get(reverse('posts:follow_index'))
        self.assertNotIn(self.post, response_non_follower.context['page_obj'])
        self.author2.get(reverse(
            'posts:profile_follow', args={self.post.author.username}
        ))
        response_follower = self.author2.get(reverse('posts:follow_index'))
        self.assertIn(self.post, response_follower.context['page_obj'])


class PaginatorViewsTest(TestCase):
    POSTS_FIRST_PAGE = 10
    POSTS_SECOND_PAGE = 3

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        posts_list = []
        cls.group = Group.objects.create(title='TestGroup', slug='test_slug')
        cls.user = User.objects.create_user(username='Pag', password='inator')
        for number in range(cls.POSTS_FIRST_PAGE + cls.POSTS_SECOND_PAGE):
            posts_list.append(Post(text=f'Тестовый текст {number}',
                                   group=cls.group,
                                   author=cls.user))
        Post.objects.bulk_create(posts_list)

    def setUp(self):
        cache.clear()
        self.client.force_login(self.user)
        self.guest_client = Client()
        self.pages_names = [
            reverse('posts:index'),
            reverse('posts:group_posts', args={self.group.slug}),
            reverse('posts:profile', args={self.user.username}),
        ]

    def test_first_page_contains_ten_records(self):
        """Количество постов на первой странице равно 10."""
        for page in self.pages_names:
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(
                    response.context['page_obj'].end_index(),
                    self.POSTS_FIRST_PAGE
                )

    def test_cecond_page_contains_ten_records(self):
        """Количество постов на второй странице равно 3."""
        for page in self.pages_names:
            with self.subTest(page=page):
                response = self.client.get(page + '?page=2')
                self.assertEqual(
                    (response.context['page_obj'].end_index()
                     - self.POSTS_FIRST_PAGE),
                    self.POSTS_SECOND_PAGE
                )
