from rest_framework.views import APIView
from rest_framework.response import Response
from .services.sequence_buffer import add_landmarks
from .services.predictor import predecir_desde_landmarks

class GesturePredictView(APIView):
    def post(self, request):
        landmarks = request.data.get("landmarks")

        if not landmarks:
            return Response({"error": "No enviaste landmarks"}, status=400)

        # Guardar este frame
        add_landmarks(landmarks)

        # Intentar predecir
        resultado = predecir_desde_landmarks()

        if resultado is None:
            return Response({"estado": "esperando 65 frames"})

        return Response(resultado)
