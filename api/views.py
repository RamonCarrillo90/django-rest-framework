from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .services.predictor import GesturePredictor

predictor = GesturePredictor()


class PredictGestureAPI(APIView):

    def post(self, request):
        frames = request.data.get("frames", None)

        if frames is None:
            return Response({"error": "No frames provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = predictor.predict(frames)
            return Response(result, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)
