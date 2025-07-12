from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from . import views

app_name = "App"

urlpatterns = [
    path("", views.home, name="home"),
    path("playlist/<int:id>/",views.playlist, name="playlist"),
    path("likedsongs",views.likedsongs, name="likedsongs"),
    path("login",views.login, name="login"),
    path("register",views.register,name="register"),
    path("logout",views.logout, name="logout"),
    path('song/<int:id>/', views.song, name='song'),
    path('playlist/<int:playlist_id>/song/<int:id>/', views.song, name='playlist_song'),
    # path("song/",views.song, name="song"),
    path("queue",views.queue,name="queue"),
    path("playsong",views.playsong,name="playsong"),
    path("verify-otp/", views.verify_otp, name="verify_otp"),
]
urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
