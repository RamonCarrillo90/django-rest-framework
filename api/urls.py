from django.urls import path
from .views import GesturePredictView
from django.urls import path
from .views import GesturePredictView, health_check

urlpatterns = [
    path('predict/', GesturePredictView.as_view(), name='predict'),
    path('health/', health_check, name='health'),
]