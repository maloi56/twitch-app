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
    WITH_SUB = 4
    VOICE_CHOICES = (
        (ALL, 'Все'),
        (OFF, 'Отключено'),
        (WITH_PREFIX, 'С приставкой'),
        (WITH_SUB, 'С подпиской')
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
    points_per_msg = models.PositiveIntegerField(verbose_name='Очки за сообщение', default=10,
                                                 help_text='Количество очков, которое получает зритель за сообщение')

    widget_count = models.PositiveIntegerField(verbose_name='Количество на виджете', default=5,
                                               validators=[MaxValueValidator(15)],
                                               help_text='Количество зрителей, отображаемые на виджете')

    points_name = models.CharField(verbose_name='Название для поинтов', default='points', max_length=32,
                                   help_text='Альтернативное название для поинтов')

    active = models.BooleanField(verbose_name='Выключатель', default=True,
                                 help_text='Включение/выключение лидерборда на виджете')

    secret = models.UUIDField(verbose_name='Секретный ключ', unique=True, null=True, blank=True,
                              help_text='Секретный ключ для WS')

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
    leaderboard = models.ForeignKey(to=Leaderboard, on_delete=models.CASCADE, related_name='leaderboard_members')
    nickname = models.CharField(verbose_name='Никнейм', max_length=255)
    points = models.PositiveIntegerField(verbose_name='Поинты', default=0)

    class Meta:
        unique_together = ('nickname', 'leaderboard',)
        verbose_name = "Зритель"
        verbose_name_plural = "Зрители"

    def __str__(self):
        return f'{self.nickname}'


class Subscription(models.Model):
    DAYS = 1
    MESSAGES_COUNT = 2

    SUBSCRIPTION_TYPES = (
        ('days', DAYS),
        ('messages_count', MESSAGES_COUNT)
    )

    channel = models.ForeignKey(to=User, verbose_name='Канал', on_delete=models.CASCADE)
    type = models.CharField(verbose_name='Тип подписки',
                            choices=SUBSCRIPTION_TYPES,
                            default=DAYS,
                            help_text='Выбор типа подписки. Подписка на дни или количество сообщений')

    value = models.PositiveIntegerField(verbose_name='Количество', default=1, help_text='Количество дней/сообщений')
    price = models.PositiveIntegerField(verbose_name='Цена', default=100, help_text='Цена за подписку')
    description = models.CharField(verbose_name='Описание', null=True, blank=True, help_text='Описание подписки')

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"


class Product(models.Model):
    channel = models.ForeignKey(to=User, verbose_name='Канал', on_delete=models.CASCADE)
    price = models.PositiveIntegerField(verbose_name='Цена', default=100, help_text='Цена за товар/услугу')
    description = models.CharField(verbose_name='Описание', null=True, blank=True, help_text='Описание товара/услуги')

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
