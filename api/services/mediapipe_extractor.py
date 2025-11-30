import mediapipe as mp
import cv2
import numpy as np
from PIL import Image
import io
import base64

class MediaPipeExtractor:
    def __init__(self):
        self.mpHolistic = mp.solutions.holistic
        self.holistic = self.mpHolistic.Holistic(
            static_image_mode=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    def extract_keypoints_from_base64(self, image_base64: str):
        """
        Extrae 81 keypoints (243 valores) desde una imagen en base64
        Retorna una lista plana de 243 valores [x,y,z,x,y,z,...]
        """
        try:
            # Decodificar imagen
            image_bytes = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convertir a numpy array
            img_array = np.array(image)
            
            # Asegurarse de que es RGB
            if len(img_array.shape) == 2:  # Escala de grises
                img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
            elif img_array.shape[2] == 4:  # RGBA
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
            
            # Procesar con MediaPipe (espera RGB)
            results = self.holistic.process(img_array)
            
            # Extraer keypoints
            keypoints = self._extract_keypoints(results)
            
            # Información de debug
            non_zero = sum(1 for i in range(0, len(keypoints), 3) 
                          if not all(keypoints[i:i+3] == [0.0, 0.0, 0.0]))
            
            print(f"✅ MediaPipe extrajo {non_zero}/81 puntos detectados")
            print(f"   Pose: {results.pose_landmarks is not None}")
            print(f"   Cara: {results.face_landmarks is not None}")
            print(f"   Mano izq: {results.left_hand_landmarks is not None}")
            print(f"   Mano der: {results.right_hand_landmarks is not None}")
            
            return keypoints
            
        except Exception as e:
            print(f"❌ Error extrayendo keypoints: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_keypoints(self, results):
        """
        Extrae exactamente 81 keypoints:
        - 33 puntos de pose (99 valores)
        - 6 puntos de cara (18 valores)
        - 21 puntos de mano izquierda (63 valores)
        - 21 puntos de mano derecha (63 valores)
        Total: 243 valores
        """
        keypoints = []
        
        # 1. Pose: 33 puntos × 3 = 99 valores
        if results.pose_landmarks:
            for lm in results.pose_landmarks.landmark:
                keypoints.extend([lm.x, lm.y, lm.z])
        else:
            keypoints.extend([0.0] * 99)
        
        # 2. Cara: 6 puntos específicos × 3 = 18 valores
        # Índices de MediaPipe Face Mesh: [1, 33, 263, 61, 291, 199]
        if results.face_landmarks:
            face_indices = [1, 33, 263, 61, 291, 199]
            for idx in face_indices:
                lm = results.face_landmarks.landmark[idx]
                keypoints.extend([lm.x, lm.y, lm.z])
        else:
            keypoints.extend([0.0] * 18)
        
        # 3. Mano izquierda: 21 puntos × 3 = 63 valores
        if results.left_hand_landmarks:
            for lm in results.left_hand_landmarks.landmark:
                keypoints.extend([lm.x, lm.y, lm.z])
        else:
            keypoints.extend([0.0] * 63)
        
        # 4. Mano derecha: 21 puntos × 3 = 63 valores
        if results.right_hand_landmarks:
            for lm in results.right_hand_landmarks.landmark:
                keypoints.extend([lm.x, lm.y, lm.z])
        else:
            keypoints.extend([0.0] * 63)
        
        return keypoints  # Total: 243 valores
    
    def close(self):
        if hasattr(self, 'holistic'):
            self.holistic.close()

# Instancia global para reutilizar
_extractor = None

def get_mediapipe_extractor():
    global _extractor
    if _extractor is None:
        _extractor = MediaPipeExtractor()
    return _extractor