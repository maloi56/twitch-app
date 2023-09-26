import redis

from datetime import timedelta
from http import HTTPStatus

from django.urls import reverse_lazy
from rest_framework.test import APITestCase
from django.utils.timezone import now
from django.conf import settings

from users.models import User, Leaderboard, BotSettings, LeaderboardMembers
from oauth2_provider.models import AccessToken
from users.serializers import LeaderboardSerializer, BotSettingsSerializer, LeaderboardSecretSerializer

r = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=1)


class UsersApiTestCase(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(username='testuser1', email='testuser1@mail.ru', password='testtesttest1')
        self.access = AccessToken.objects.create(user=self.user,
                                                 token='uN2yQEkuAn9FGwJlfa2lpEtsqxb2Az',
                                                 expires=now() + timedelta(hours=1), )
        self.temp_user = User.objects.create_user(username='tempUser1',
                                                  email='tempUser1@mail.ru',
                                                  password='testtesttest1')
        self.headers = {'Authorization': 'Bearer ' + self.access.token}

    def clear_cache(self):
        keys_with_match = r.keys(f"*{self.user.username}*")
        for key in keys_with_match:
            r.delete(key)

    def test_get_leaderboard(self):
        self.clear_cache()

        leaderboard = Leaderboard.objects.get(channel=self.user)

        # get leaderboard
        url = reverse_lazy('leaderboard-detail', args=(self.user.username,))
        response = self.client.get(url, headers=self.headers)
        serializer_leaderboard = LeaderboardSerializer(leaderboard).data
        self.assertEquals(response.data, serializer_leaderboard)

        # check permissions
        url = reverse_lazy('leaderboard-detail', args=(self.temp_user.username,))
        response = self.client.get(url, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_leaderboard_secret(self):
        self.clear_cache()

        # get leaderboard_secret
        url = reverse_lazy('leaderboard-secret-detail', args=(self.user.username,))
        response = self.client.get(url, headers=self.headers)

        leaderboard = Leaderboard.objects.get(channel=self.user)
        serializer_secret = LeaderboardSecretSerializer(leaderboard).data
        self.assertEquals(response.data, serializer_secret)

        # change secret
        query_param = '?new=1'
        url = reverse_lazy('leaderboard-secret-detail', args=(self.user.username,)) + query_param
        response = self.client.get(url, headers=self.headers)
        self.assertNotEquals(response.data, serializer_secret)

        # check permissions
        url = reverse_lazy('leaderboard-detail', args=(self.temp_user.username,))
        response = self.client.get(url, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_update_leaderboard(self):
        self.clear_cache()


        url = reverse_lazy('leaderboardmembers-list') + f'?channel={self.user.username}'
        data = {'channel': {
            'username': 'newnick'}
        }

        # test update leaderboard
        response = self.client.patch(url,
                                     headers=self.headers,
                                     data=data,
                                     format='json')
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)

    def test_get_settings(self):
        self.clear_cache()


        self.settings = BotSettings.objects.get(user=self.user)
        serializer_settings = BotSettingsSerializer(self.settings).data

        # get settings
        url = reverse_lazy('botsettings-detail', args=(self.user.username,))
        response = self.client.get(url, headers=self.headers)
        self.assertEquals(response.data, serializer_settings)

        # test permissions
        url = reverse_lazy('botsettings-detail', args=(self.temp_user.username,))
        response = self.client.get(url, headers=self.headers)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_update_settings(self):
        self.clear_cache()

        url = reverse_lazy('botsettings-detail', args=(self.user.username,))
        get_response = self.client.get(url, headers=self.headers)
        # test update
        data = {
            'voice_status': 2,
            'command': 'privet',
            'language': 'eng',
            'volume': '0.5',
            'rate': '0.3',
            'pitch': '0.4',
            'delay': 5
        }
        response = self.client.patch(url,
                                     headers=self.headers,
                                     data=data,
                                     format='json')
        self.assertNotEquals(get_response.data, response.data)

        # test wrong update
        response = self.client.patch(url,
                                     headers=self.headers,
                                     data={'voice_status': 5},
                                     format='json')
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

        # check permissions
        url = reverse_lazy('botsettings-detail', args=(self.temp_user.username,))
        response = self.client.patch(url,
                                     headers=self.headers,
                                     data={'voice_status': 3},
                                     format='json')
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
