from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator

from django.db.models.signals import post_save
from django.dispatch import receiver

# from allauth.socialaccount.models import SocialAccount


class UserInfo(models.Model):
    user = models.OneToOneField(User, verbose_name='Канал', on_delete=models.CASCADE)
    voice_status = models.BooleanField(verbose_name='Озвучка чата', default=False)

    class Meta:
        verbose_name = "Параметры приложения"
        verbose_name_plural = "Параметры приложения"

    def __str__(self):
        return f'Канал {self.user}'

#
# @receiver(post_save, sender=SocialAccount)
# def update_userinfo(sender, instance, **kwargs):
#     user = instance.user
#     if not UserInfo.objects.filter(user=user).exists():
#         UserInfo.objects.create(user=user)


class Leaderboard(models.Model):
    channel = models.ForeignKey(to=User, verbose_name='Канал', on_delete=models.CASCADE)
    created = models.DateTimeField(verbose_name='Дата создания', auto_created=True)

    def __str__(self):
        return f'Лидерборд, созданный {self.created} на канале {self.channel}'

    class Meta:
        verbose_name = "Лидерборд"
        verbose_name_plural = "Лидерборды"


class LeaderboardMembers(models.Model):
    DEFAULT_EXP_PER_LVL = 125
    DEFAULT_K = 0.125

    leaderboard = models.ForeignKey(to=Leaderboard, on_delete=models.CASCADE, related_name='leaderboard_members')
    nickname = models.CharField(verbose_name='Никнейм', max_length=255)
    experience = models.IntegerField(verbose_name='Очки опыта',
                                     default=0,
                                     validators=[MinValueValidator(0)])
    level = models.IntegerField(verbose_name='Уровень',
                                default=1,
                                validators=[MinValueValidator(1), MaxValueValidator(999)])

    @classmethod
    def __get_level_boarder(cls, level):
        return level * cls.DEFAULT_EXP_PER_LVL * cls.DEFAULT_K

    def add_exp(self, value):
        current_exp = self.experience + value
        while current_exp > LeaderboardMembers.__get_level_boarder(self.level):
            current_exp = current_exp - LeaderboardMembers.__get_level_boarder(self.level)
            self.level += 1
        self.experience = current_exp
        self.save()

    class Meta:
        unique_together = ('nickname', 'leaderboard',)
