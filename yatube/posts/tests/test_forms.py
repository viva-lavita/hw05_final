import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache

from posts.models import Comment, Post, Group, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        self.post = Post.objects.create(
            text='Тестовый текст',
            author=User.objects.create_user(username='Foo', password='barbaz'),
            group=Group.objects.create(title='TestGroup', slug='test_slug'),
        )
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post.author)
        self.form_data = {'text': 'Новый текст записанный в форму',
                          'group': self.post.group.id,
                          'image': self.uploaded}

    def tearDown(self):
        Post.objects.all().delete()
        Group.objects.all().delete()

    def test_create_post(self):
        """Проверка создания поста."""
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=self.form_data, follow=True
        )
        self.assertRedirects(
            response, reverse('posts:profile',
                              args={self.post.author.username})
        )
        new_post = Post.objects.latest('id')
        self.assertEqual(new_post.text, self.form_data['text'])
        self.assertEqual(new_post.group.id, self.form_data['group'])
        self.assertTrue(new_post.image)

    def test_post_edit(self):
        """
        Проверка, что произошло редактирвоание поста,
        а не создание нового.
        """
        response = self.authorized_client.post(
            reverse('posts:post_edit', args={self.post.id}),
            data=self.form_data, follow=True
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args={self.post.id})
        )
        corrected_post = Post.objects.filter(pk=self.post.id).first()
        self.assertEqual(corrected_post.text, self.form_data['text'])
        self.assertEqual(corrected_post.group.id, self.form_data['group'])

    def test_comment_post_form(self):
        response = self.authorized_client.post(
            reverse('posts:add_comment', args={self.post.id}),
            data=self.form_data, follow=True
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args={self.post.id})
        )
        comment = Comment.objects.latest('pk')
        self.assertEqual(comment.text, self.form_data['text'])
