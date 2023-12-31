"""
URL configuration for twitch project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework import routers

from users.views import (BotSettingsViewSet, LeaderBoardMembersModalViewSet,
                         LeaderBoardModalViewSet, LeaderboardSecret, oauth,
                         test)

from .yasg import urlpatterns as doc_urls

urlpatterns = [
    path('admin/', admin.site.urls),
    path('oauth/', oauth),
    path('test/', test),
    re_path(r'^auth/', include('drf_social_oauth2.urls', namespace='drf')),

]

urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]

router = routers.DefaultRouter()
router.register(r'api/leaderboard', LeaderBoardMembersModalViewSet)
router.register(r'api/leaderboard/settings', LeaderBoardModalViewSet)
router.register(r'api/leaderboard/secret', LeaderboardSecret, basename='leaderboard-secret')
router.register(r'api/settings', BotSettingsViewSet)

urlpatterns += router.urls
urlpatterns += doc_urls
