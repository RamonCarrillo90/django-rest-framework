from django.urls import path
from .views import PredictGestureAPI, GesturePredictView, health_check

urlpatterns = [
    path('health/', health_check, name='health'),  # ✅ Health check endpoint
    path('predict/', GesturePredictView.as_view(), name='predict'),  # ✅ Endpoint nuevo con MediaPipe
    path('predict-frames/', PredictGestureAPI.as_view(), name='predict-frames'),  # Endpoint anterior
]