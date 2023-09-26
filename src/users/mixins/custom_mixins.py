from django.core.cache import cache


class CachedObjectMixin:
    ONE_WEEK = 7 * 24 * 3600

    def get_object(self):
        key = f'{self.__class__.__name__}_{self.kwargs[self.lookup_field]}'
        obj = cache.get(key)
        if not obj:
            obj = super().get_object()
            cache.set(key, obj, self.ONE_WEEK)
        return obj
