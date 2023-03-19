from django.test import TestCase

from ..models import Comment, Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            text='Тестовый коммент',
            post=cls.post,
            author=cls.post.author
        )
        cls.object_names = {
            cls.post: 'Тестовый пост',
            cls.group: 'Тестовая группа',
            cls.user: 'auth'
        }
        cls.field_verbose_and_help_text = {
            cls.post._meta.get_field('text').verbose_name: 'Текст поста',
            cls.post._meta.get_field('text').help_text: 'Введите текст поста',
            cls.post._meta.get_field('group').verbose_name: 'Группа',
            cls.post._meta.get_field('group').help_text:
            'Группа, к которой будет относиться пост',
            cls.comment._meta.get_field('text').help_text:
            'Введите текст комментария',
        }

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        for field, expected_field in self.object_names.items():
            self.assertEqual(str(field), expected_field)

    def test_help_text_and_verbose_name(self):
        for field, expected_field in self.field_verbose_and_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(field, expected_field)
