from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .services.predictor import GesturePredictor
from .services.sequence_buffer import add_landmarks, get_buffer_size, get_sequence, clear_buffer
from .services.mediapipe_extractor import get_mediapipe_extractor
import logging

logger = logging.getLogger(__name__)

# Lazy loading del predictor para evitar que crashee todo si falla
_predictor = None

def get_predictor():
    """Obtiene la instancia del predictor (lazy loading)"""
    global _predictor
    if _predictor is None:
        logger.info("Inicializando GesturePredictor...")
        try:
            _predictor = GesturePredictor()
            logger.info("✅ GesturePredictor inicializado exitosamente")
        except Exception as e:
            logger.error(f"❌ Error inicializando GesturePredictor: {e}", exc_info=True)
            raise
    return _predictor


@method_decorator(csrf_exempt, name='dispatch')
class PredictGestureAPI(APIView):
    """Endpoint que recibe frames directamente (método anterior)"""

    def post(self, request):
        try:
            logger.info("📥 POST /api/predict-frames/ - Recibiendo request")
            frames = request.data.get("frames", None)

            if frames is None:
                logger.warning("❌ No se proporcionaron frames")
                return Response({"error": "No frames provided"}, status=status.HTTP_400_BAD_REQUEST)

            logger.info(f"✅ Frames recibidos: {len(frames)}")

            predictor = get_predictor()
            result = predictor.predict(frames)

            logger.info(f"✅ Predicción exitosa: {result.get('gesto', 'N/A')}")
            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"❌ Error en PredictGestureAPI: {e}", exc_info=True)
            return Response(
                {"error": str(e), "detail": "Error al procesar la predicción"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class GesturePredictView(APIView):
    """Endpoint que recibe imagen en base64 y usa MediaPipe (NUEVO)"""

    def post(self, request):
        try:
            logger.info("📥 POST /api/predict/ - Recibiendo request")
            data = request.data

            # OPCIÓN 1: Recibir imagen en base64
            if 'image' in data:
                logger.info("🖼️ Procesando imagen en base64")
                image_base64 = data['image']

                # Extraer landmarks con MediaPipe
                extractor = get_mediapipe_extractor()
                landmarks = extractor.extract_keypoints_from_base64(image_base64)

                if landmarks is None:
                    logger.warning("❌ No se pudieron extraer landmarks de la imagen")
                    return Response(
                        {'error': 'No se pudieron extraer landmarks de la imagen'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # Verificar que tenemos 243 valores (81 puntos × 3)
                if len(landmarks) != 243:
                    logger.warning(f"❌ Landmarks incorrectos: {len(landmarks)} valores (esperado: 243)")
                    return Response(
                        {
                            'error': f'Landmarks incorrectos: {len(landmarks)} valores',
                            'esperado': 243
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                logger.info(f"✅ Landmarks extraídos: {len(landmarks)} valores")

            # OPCIÓN 2: Recibir landmarks directamente
            elif 'landmarks' in data:
                logger.info("📊 Recibiendo landmarks directamente")
                landmarks = data['landmarks']

                if len(landmarks) != 243:
                    logger.warning(f"❌ Landmarks incorrectos: {len(landmarks)} valores (esperado: 243)")
                    return Response(
                        {
                            'error': f'Se esperan 243 valores, se recibieron {len(landmarks)}'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                logger.info(f"✅ Landmarks recibidos: {len(landmarks)} valores")
            else:
                logger.warning("❌ No se proporcionó 'image' ni 'landmarks'")
                return Response(
                    {'error': 'Se requiere "image" o "landmarks"'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Guardar frame en el buffer
            add_landmarks(landmarks)

            # Verificar si tenemos 65 frames
            buffer_size = get_buffer_size()
            logger.info(f"📦 Buffer size: {buffer_size}/65 frames")

            if buffer_size < 65:
                return Response({
                    'estado': f'esperando {65 - buffer_size} frames más',
                    'frames_actuales': buffer_size,
                    'frames_requeridos': 65
                })

            # Obtener secuencia completa
            sequence = get_sequence()

            if sequence is None:
                logger.warning("❌ No hay suficientes frames en buffer")
                return Response(
                    {'error': 'No hay suficientes frames en buffer'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Predecir con el modelo
            logger.info("🔮 Iniciando predicción...")
            predictor = get_predictor()
            resultado = predictor.predict(sequence)

            logger.info(f"✅ Predicción exitosa: {resultado.get('gesto', 'N/A')} (confianza: {resultado.get('confianza', 0):.2f})")

            # Limpiar buffer después de predicción exitosa
            clear_buffer()
            logger.info("🧹 Buffer limpiado")

            return Response({
                'estado': 'prediccion',
                'gesto': resultado['gesto'],
                'confianza': resultado['confianza'],
                'top_3': resultado.get('top_3', [])
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"❌ Error en GesturePredictView: {e}", exc_info=True)
            return Response(
                {'error': str(e), 'detail': 'Error al procesar la predicción'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@csrf_exempt
def health_check(request):
    """
    Endpoint de health check para verificar que el servidor está funcionando
    """
    try:
        logger.info("💚 GET /api/health/ - Health check")

        # Verificar estado del predictor (sin inicializarlo si no está listo)
        predictor_status = "not_initialized"
        if _predictor is not None:
            predictor_status = "ready"

        # Verificar buffer
        buffer_size = get_buffer_size()

        response_data = {
            "status": "healthy",
            "service": "Django REST Framework - Gesture Recognition API",
            "version": "1.4",
            "predictor": predictor_status,
            "buffer_size": buffer_size,
            "endpoints": {
                "predict": "/api/predict/",
                "predict_frames": "/api/predict-frames/",
                "health": "/api/health/"
            }
        }

        logger.info(f"✅ Health check OK - Predictor: {predictor_status}")
        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ Error en health check: {e}", exc_info=True)
        return Response(
            {
                "status": "unhealthy",
                "error": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )