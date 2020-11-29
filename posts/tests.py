from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files import File
from django.test import TestCase, Client
from django.urls import reverse

from .models import Post, Group, Follow

import mock

User = get_user_model()


class DefaultSetUp(TestCase):
    def defaultSetUp(self):
        cache.clear()
        self.auth_client = Client()
        self.client_logout = Client()
        self.user = User.objects.create_user(
            username='Barney',
        )
        self.auth_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='testgroup'
        )


class TestPost(DefaultSetUp):

    def setUp(self):
        self.defaultSetUp()

    def test_profile(self):
        response = self.client_logout.get(
            reverse('profile', kwargs=dict(username=self.user.username)))
        self.assertEqual(response.status_code, 200)

    def test_new_post(self):
        response = self.auth_client.post(reverse('new_post'),
                                         data={'text': 'post for test'})
        self.assertEqual(response.status_code, 302)
        response = self.auth_client.get(reverse('index'))
        self.assertContains(response, 'post for test', status_code=200)

    def test_new_post_logout(self):
        response = self.client_logout.post(reverse('new_post'),
                                           data={'text': 'text for test'})
        posts = Post.objects.all()
        for post in posts:
            self.assertNotEqual(post.text, 'text for test')
        self.assertRedirects(response, '/auth/login/?next=/new/', 302)

    def test_post_published(self):
        image = mock.MagicMock(spec=File)
        image.name = 'test_image.jpg'
        post = Post.objects.create(text='test text', author=self.user,
                                   group=self.group,
                                   image=image)
        self.assertEqual(Post.objects.count(), 1)
        self.check_all_page(post.id, post.text, post.author, post.group)

    def test_post_edit(self):
        image = mock.MagicMock(spec=File)
        image.name = 'test_image_p.jpg'
        post = Post.objects.create(text='test text', author=self.user,
                                   group=self.group, image=image)
        edit_text = 'edit test text'
        post_id = post.id
        new_group = Group.objects.create(
            title='Матрёшка',
            slug='matreshka'
        )
        self.auth_client.post(
            reverse(
                'post_edit',
                kwargs={
                    'username': self.user.username,
                    'post_id': post_id,
                }
            ),
            data={'group': new_group.id, 'text': edit_text}
        )

    def test_load_not_image(self):
        image = mock.MagicMock(spec=File)
        image.name = 'test_image_p.doc'
        response = self.auth_client.post(
            reverse(
                'new_post',
            ),
            data={'group': self.group.id, 'text': 'text',
                  'author': self.auth_client, 'image': image}, follow=True
        )
        posts_count = Post.objects.count()
        self.assertFormError(
            response, form='form', field='image',
            errors='Загрузите правильное изображение. '
                   'Файл, который вы загрузили, поврежден'
                   ' или не является изображением.'
        )
        self.assertEqual(posts_count, 0)

    def check_all_page(self, post_id, text, author, group):
        for url in (
                reverse('index'),
                reverse('profile', kwargs={'username': self.user.username}),
                reverse('post', kwargs={
                    'username': self.user.username,
                    'post_id': post_id,
                }),
        ):
            with self.subTest(url=url):
                response = self.auth_client.get(url)
                self.assertContains(response, 'img')
                if 'paginator' in response.context:
                    posts = response.context['paginator'].object_list[0]
                    self.assertEqual(Post.objects.count(), 1)
                else:
                    posts = response.context['post']
                self.assertEqual(posts.text, text)
                self.assertEqual(posts.author, author)
                self.assertEqual(posts.group, group)


class TestErrorPage(DefaultSetUp):
    def setUp(self):
        self.defaultSetUp()

    def test_404(self):
        response = self.auth_client.get('something/really/weird/')
        self.assertEqual(response.status_code, 404)

    def test_cache_index(self):
        response = self.auth_client.get(reverse('index'))
        self.auth_client.post(
            reverse('new_post'),
            data={
                'text': 'cache test',
                'group': self.group.id
            }
        )
        self.assertNotContains(response, 'cache test')


class TestFollow(DefaultSetUp):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
                        username="fortest1", password="qwerty123"
                )
        self.user2 = User.objects.create_user(
                        username="fortest2", password="321654"
                )
        self.user3 = User.objects.create_user(
                        username="TestUser3", password="987654"
                )
        self.post = Post.objects.create(text="Test post", author=self.user3)


    def test_follow_unfollow(self):
        self.client.login(username="fortest1", password="qwerty123")
        self.client.get('/fortest2/follow')
        response = self.client.get('/fortest1/')
        self.assertEqual(response.status_code, 200)
        self.client.get('/fortest2/unfollow')
        response = self.client.get('/fortest1/')
        self.assertEqual(response.status_code, 200)
    

    def test_post_following(self):
        Post.objects.create(text='Follower text', author=self.other_user)
        response = self.auth_client.get(reverse('follow_index'), follow=True)
        self.assertNotContains(response, 'Follower text')
        self.auth_client.post(
            reverse('profile_follow',
                    kwargs={
                        'username': self.other_user,
                    }),
        )
        response = self.auth_client.get(reverse('follow_index'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Follower text')

    def test_add_comment_logout(self):
        post = Post.objects.create(text='Follower text',
                                   author=self.other_user)
        response = self.client_logout.post(
            reverse('add_comment',
                    kwargs={
                        'username': self.other_user,
                        'post_id': post.id
                    }),
            data={
                'text': 'comment test',
            },
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'comment test')
