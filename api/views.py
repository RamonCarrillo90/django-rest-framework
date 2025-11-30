from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services.sequence_buffer import add_landmarks, get_buffer_size
from .services.predictor import predecir_desde_landmarks
from .services.mediapipe_extractor import get_mediapipe_extractor
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET', 'POST'])
def health_check(request):
    """Endpoint de prueba"""
    return Response({
        'status': 'ok',
        'message': 'Servidor funcionando',
        'method': request.method
    })




class GesturePredictView(APIView):
    def post(self, request):
        try:
            data = request.data
            
            # OPCIÓN 1: Recibir imagen en base64 (NUEVO)
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
                
                # Verificar que tenemos 243 valores
                if len(landmarks) != 243:
                    return Response(
                        {
                            'error': f'Landmarks incorrectos: {len(landmarks)} valores',
                            'esperado': 243
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # OPCIÓN 2: Recibir landmarks directamente (ANTERIOR)
            elif 'landmarks' in data:
                landmarks = data['landmarks']
                
                if len(landmarks) != 243:
                    return Response(
                        {
                            'error': f'Se esperan 243 valores, se recibieron {len(landmarks)}',
                            'nota': 'Asegúrate de enviar 81 puntos × 3 coordenadas'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                return Response(
                    {
                        'error': 'Se requiere "image" (base64) o "landmarks" (array)',
                        'ejemplo_image': '{"image": "base64_string_here"}',
                        'ejemplo_landmarks': '{"landmarks": [x1,y1,z1,x2,y2,z2,...]}'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Guardar frame en el buffer
            add_landmarks(landmarks)
            
            # Intentar predecir
            resultado = predecir_desde_landmarks()
            
            if resultado is None:
                # Aún no hay suficientes frames
                buffer_size = get_buffer_size()
                return Response({
                    'estado': f'esperando {65 - buffer_size} frames más',
                    'frames_actuales': buffer_size,
                    'frames_requeridos': 65
                })
            
            # Predicción completada
            return Response({
                'estado': 'prediccion',
                'gesto': resultado['gesto'],
                'confianza': resultado['confianza'],
                'top_3': resultado['top_3']
            })
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )