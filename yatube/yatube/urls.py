from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('about/', include('about.urls', namespace='about')),
    path('group/slug:slug', include('posts.urls', namespace='group_posts')),
    path('profile/str:username', include('posts.urls', namespace='profile')),
    path('posts/int:post_id', include('posts.urls', namespace='post_detail')),
    path('admin/', admin.site.urls),
    path('auth/', include('users.urls', namespace='user')),
    path('auth/', include('django.contrib.auth.urls')),
    path('', include('posts.urls', namespace='index')),
]

handler404 = 'core.views.page_not_found'
handler403 = 'core.views.permission_denied'
handler500 = 'core.views.server_error'
