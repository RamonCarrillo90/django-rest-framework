from django.urls import path
from .views import GesturePredictView

urlpatterns = [
    path("predict/", GesturePredictView.as_view()),
]
