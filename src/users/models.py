import uuid

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator

from django.db.models.signals import post_save
from django.dispatch import receiver


# from allauth.socialaccount.models import SocialAccount


class BotSettings(models.Model):
    ALL = 1
    OFF = 2
    WITH_PREFIX = 3
    VOICE_CHOICES = (
        (ALL, 'Все'),
        (OFF, 'Отключено'),
        (WITH_PREFIX, 'С приставкой')
    )

    RU = 'ru'
    ENG = 'eng'
    FR = 'fr'
    DE = 'de'
    LANG_CHOICES = ((RU, 'Русский'),
                    (ENG, 'Английский'),
                    (FR, 'Французский'),
                    (DE, 'Немецкий'),)

    user = models.OneToOneField(User, verbose_name='Канал', on_delete=models.CASCADE, related_name='settings')
    voice_status = models.IntegerField(verbose_name='Озвучка чата', choices=VOICE_CHOICES, default=ALL)
    command = models.CharField(verbose_name='Команда', max_length=36, default='say')
    language = models.CharField(verbose_name='Язык озвучивания', choices=LANG_CHOICES, default=RU)

    volume = models.DecimalField(verbose_name='Громкость',
                                 default=0.5,
                                 max_digits=2,
                                 decimal_places=1,
                                 validators=[MinValueValidator(0), MaxValueValidator(1)],
                                 help_text='Настройка громкости')

    rate = models.DecimalField(verbose_name='Частота',
                               default=1.0,
                               max_digits=2,
                               decimal_places=1,
                               validators=[MinValueValidator(0), MaxValueValidator(2)],
                               help_text='Настройка частоты')

    pitch = models.DecimalField(verbose_name='Подача',
                                default=1.0,
                                max_digits=2,
                                decimal_places=1,
                                validators=[MinValueValidator(0), MaxValueValidator(2)],
                                help_text='Настройка подачи')

    delay = models.IntegerField(verbose_name='Задержка',
                                default=5,
                                validators=[MinValueValidator(0)],
                                help_text='Настройка задержки озвучивания сообщений в секундах')

    class Meta:
        verbose_name = "Параметры бота"
        verbose_name_plural = "Параметры бота"

    def __str__(self):
        return f'Канал {self.user}'


@receiver(post_save, sender=User)
def update_userinfo(sender, instance, **kwargs):
    user = instance
    if not BotSettings.objects.filter(user=user).exists() and not Leaderboard.objects.filter(channel=user).exists():
        BotSettings.objects.create(user=user)
        Leaderboard.objects.create(channel=user)


class Leaderboard(models.Model):
    channel = models.ForeignKey(to=User, verbose_name='Канал', on_delete=models.CASCADE)
    secret = models.UUIDField(unique=True, null=True, blank=True)

    def update_secret(self):
        self.secret = uuid.uuid4()
        self.save()
        return self.secret

    def __str__(self):
        return f'Лидерборд на канале {self.channel.username}'

    class Meta:
        verbose_name = "Лидерборд"
        verbose_name_plural = "Лидерборды"


class LeaderboardMembers(models.Model):
    DEFAULT_EXP_PER_LVL = 125
    DEFAULT_K = 1.125

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
        return round(level * cls.DEFAULT_EXP_PER_LVL * cls.DEFAULT_K)

    def add_exp(self, value):
        current_exp = self.experience + value
        while current_exp >= LeaderboardMembers.__get_level_boarder(self.level):
            current_exp = round(current_exp - LeaderboardMembers.__get_level_boarder(self.level))
            self.level += 1
        self.experience = current_exp
        self.save()

    class Meta:
        unique_together = ('nickname', 'leaderboard',)
