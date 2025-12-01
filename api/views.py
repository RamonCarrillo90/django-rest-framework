from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services.predictor import GesturePredictor
from .services.sequence_buffer import add_landmarks, get_buffer_size, get_sequence
from .services.mediapipe_extractor import get_mediapipe_extractor

predictor = GesturePredictor()


class PredictGestureAPI(APIView):
    """Endpoint que recibe frames directamente (método anterior)"""
    
    def post(self, request):
        frames = request.data.get("frames", None)

        if frames is None:
            return Response({"error": "No frames provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            result = predictor.predict(frames)
            return Response(result, status=200)

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class GesturePredictView(APIView):
    """Endpoint que recibe imagen en base64 y usa MediaPipe (NUEVO)"""
    
    def post(self, request):
        try:
            data = request.data
            
            # OPCIÓN 1: Recibir imagen en base64
            if 'image' in data:
                image_base64 = data['image']
                
                # Extraer landmarks con MediaPipe
                extractor = get_mediapipe_extractor()
                landmarks = extractor.extract_keypoints_from_base64(image_base64)
                
                if landmarks is None:
                    return Response(
                        {'error': 'No se pudieron extraer landmarks de la imagen'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Verificar que tenemos 243 valores (81 puntos × 3)
                if len(landmarks) != 243:
                    return Response(
                        {
                            'error': f'Landmarks incorrectos: {len(landmarks)} valores',
                            'esperado': 243
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # OPCIÓN 2: Recibir landmarks directamente
            elif 'landmarks' in data:
                landmarks = data['landmarks']
                
                if len(landmarks) != 243:
                    return Response(
                        {
                            'error': f'Se esperan 243 valores, se recibieron {len(landmarks)}'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {'error': 'Se requiere "image" o "landmarks"'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Guardar frame en el buffer
            add_landmarks(landmarks)
            
            # Verificar si tenemos 65 frames
            buffer_size = get_buffer_size()
            
            if buffer_size < 65:
                return Response({
                    'estado': f'esperando {65 - buffer_size} frames más',
                    'frames_actuales': buffer_size,
                    'frames_requeridos': 65
                })
            
            # Obtener secuencia completa
            sequence = get_sequence()
            
            if sequence is None:
                return Response(
                    {'error': 'No hay suficientes frames en buffer'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Predecir con el modelo
            resultado = predictor.predict(sequence)
            
            return Response({
                'estado': 'prediccion',
                'gesto': resultado['prediction'],
                'confianza': resultado['confidence']
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )