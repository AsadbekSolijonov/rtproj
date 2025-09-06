from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.views.generic import TemplateView, RedirectView

from chat.views import MessageViewSet

router = DefaultRouter()
router.register('messages', MessageViewSet, basename='message')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path("", TemplateView.as_view(template_name='index.html')),
    # path("redirect/", RedirectView.as_view(url="/static/index.html")),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
