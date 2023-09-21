import redis
import logging

from celery import shared_task
from django.conf import settings

from users.models import LeaderboardMembers, Leaderboard

logger = logging.getLogger(__name__)

redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=2)


@shared_task(name='update_points')
def update_points(channel):
    '''Обновление очков пользователей'''

    try:
        logger.info('Task started: update_points')
        leaderboard = Leaderboard.objects.get(channel__username=channel)
        viewers = dict([(k.decode('utf-8'), int(v)) for k, v in redis_client.hgetall(channel).items()])
        if len(viewers) > 0:
            objects_to_insert = [LeaderboardMembers(leaderboard=leaderboard, nickname=nickname) for nickname in list(viewers)]
            LeaderboardMembers.objects.bulk_create(objects_to_insert, ignore_conflicts=True)
            obj_to_update = list(LeaderboardMembers.objects.filter(leaderboard=leaderboard, nickname__in=list(viewers)))
            for obj in obj_to_update:
                obj.points = obj.points + viewers[obj.nickname]
            logger.info(obj_to_update)
            LeaderboardMembers.objects.bulk_update(obj_to_update, ['points'])
            redis_client.delete(channel)
        logger.info('Task completed: update_points')
    except Exception as e:
        logger.error(f'Error in update_points: {e}')
