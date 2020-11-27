from django.contrib.auth.models import User
from django.shortcuts import reverse
from django.test import TestCase
from django.test import Client

from .fake_data import FakeData
from .models import Post, Group

#новые тесты находятся в папке tests в именованных файлах

class TestMethods(TestCase):

    fake_data = FakeData()

    fake_username = fake_data.fake_username
    fake_email = fake_data.fake_email
    fake_password = fake_data.fake_password
    fake_text = fake_data.fake_text
    fake_slug = fake_data.fake_slug

    def check_post_data(self, urls, text, group, author):

        for url in urls:
            response = self.client.get(reverse(url))
            paginator = response.context.get("paginator")

            if paginator is not None:
                post = response.context["page"][0]
            else:
                post = response.context["post"]

            self.assertEqual(post.text, text)
            self.assertEqual(post.author, author)
            self.assertEqual(post.group, group)

    def setUp(self, fake_username=fake_username, fake_email=fake_email,
              fake_password=fake_password, fake_slug=fake_slug):
        self.client = Client()
        self.user = User.objects.create_user(
            username=fake_username,
            email=fake_email,
            password=fake_password
        )
        self.group = Group.objects.create(
            slug=fake_slug,
            title="Test group",
            description="Test group description"
        )

    def test_profile(self):
        """Проверка создания персональной страницы после регистрации"""
        response = self.client.get(reverse("profile", kwargs={"username": self.fake_username}))
        self.assertEqual(
            response.status_code,
            200,
            msg="Страница не создана"
        )

    def test_authorization_post(self):
        """Возможность публикации авторизованным пользователем"""
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("new_post"),
            {
                "text": "text",
                "group": self.group.id
            },
            follow=True
        )
        self.assertEqual(
            response.status_code,
            200,
            msg="Публикация невозможна"
        )
        self.assertEqual(Post.objects.count(), 1)
        last_post = Post.objects.first()
        self.assertEqual(last_post.text, "text")
        self.assertEqual(last_post.author, self.user)
        self.assertEqual(last_post.group, self.group)

    def test_non_authorization_post(self):
        """Невозможность публикации неавторизованным пользователем
        (проверка редиректа)"""
        response = self.client.post(
            reverse("new_post"),
            {
                "text": "text",
                "group": self.group.id
            },
            follow=True
        )
        self.assertRedirects(response, "/auth/login/?next=/new/", 302, 200)
        self.assertFalse(Post.objects.exists())

    def test_disp_post(self, fake_text=fake_text):
        """После публикации поста новая запись появляется на главной странице
        сайта (index), на персональной странице пользователя (profile),
        и на отдельной странице поста (post)"""
        self.post = Post.objects.create(
            text=fake_text,
            author=self.user,
            group=self.group
        )
        urls = (
            reverse("index"),
            reverse("profile",  kwargs={"username": self.user.username}),
            reverse("post",  kwargs={"username": self.user.username, "post_id": self.post.id})
        )
        text = self.post.text
        group = self.group
        author = self.post.author
        self.check_post_data(urls, text, group, author)

    def test_update_post(self, fake_text=fake_text):
        """Возможность редактирования поста авторизованным пользователем,
        проверка изменений на всех страницах"""
        self.post = Post.objects.create(
            text=fake_text,
            author=self.user,
            group=self.group
        )
        self.client.force_login(self.user)
        self.client.post(
            reverse(
                "post_edit",
                kwargs={
                    "username": self.user.username,
                    "post_id": self.post.id}
            ),
            {
                "text": f"Update {fake_text}",
                "group": ""
            },
            follow=True)
        urls = (
            reverse("index"),
            reverse("profile", kwargs={"username": self.user.username}),
            reverse("post",  kwargs={"username": self.user.username, "post_id": self.post.id})
        )
        self.post = Post.objects.last()
        text = self.post.text
        group = self.post.group
        author = self.post.author
        self.check_post_data(urls, text, group, author)

    def tearDown(self, fake_username=fake_username, fake_text=fake_text,
                 fake_email=fake_email, fake_password=fake_password,
                 fake_slug=fake_slug):
        User.objects.filter(
            username=fake_username,
            email=fake_email,
            password=fake_password
        ).delete()

        Post.objects.filter(
            text=fake_text,
            group=self.group,
            author=self.user
        ).delete()

        Group.objects.filter(
            slug=fake_slug
        ).delete()
