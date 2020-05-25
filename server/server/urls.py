from django.urls import include, path
from django.contrib import admin

admin.autodiscover()

# yapf: disable
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('auvsi_suas.views.urls', namespace="auvsi_suas")),
]
# yapf: enable
