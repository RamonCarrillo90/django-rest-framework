from django.urls import path
from .views import PredictGesture

urlpatterns = [
    path('predict/', PredictGesture.as_view()),
]

