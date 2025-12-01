import mediapipe as mp
import cv2
import numpy as np
from PIL import Image
import io
import base64

class MediaPipeExtractor:
    def __init__(self):
        try:
            self.mpHolistic = mp.solutions.holistic
            self.holistic = self.mpHolistic.Holistic(
                static_image_mode=True,
                model_complexity=0,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            print("✅ MediaPipe inicializado")
        except Exception as e:
            print(f"❌ Error inicializando MediaPipe: {e}")
            raise
    
    def extract_keypoints_from_base64(self, image_base64: str):
        try:
            # Decodificar imagen
            image_bytes = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Redimensionar para mejor rendimiento
            image.thumbnail((640, 640), Image.Resampling.LANCZOS)
            
            # Convertir a numpy array
            img_array = np.array(image)
            
            # Asegurarse de que es RGB
            if len(img_array.shape) == 2:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
            elif img_array.shape[2] == 4:
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
            
            # Procesar con MediaPipe
            results = self.holistic.process(img_array)
            
            # Extraer keypoints
            keypoints = self._extract_keypoints(results)
            
            return keypoints
            
        except Exception as e:
            print(f"❌ Error extrayendo keypoints: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_keypoints(self, results):
        keypoints = []
        
        # Pose: 33 puntos × 3 = 99 valores
        if results.pose_landmarks:
            for lm in results.pose_landmarks.landmark:
                keypoints.extend([lm.x, lm.y, lm.z])
        else:
            keypoints.extend([0.0] * 99)
        
        # Cara: 6 puntos × 3 = 18 valores
        if results.face_landmarks:
            face_indices = [1, 33, 263, 61, 291, 199]
            for idx in face_indices:
                lm = results.face_landmarks.landmark[idx]
                keypoints.extend([lm.x, lm.y, lm.z])
        else:
            keypoints.extend([0.0] * 18)
        
        # Mano izquierda: 21 puntos × 3 = 63 valores
        if results.left_hand_landmarks:
            for lm in results.left_hand_landmarks.landmark:
                keypoints.extend([lm.x, lm.y, lm.z])
        else:
            keypoints.extend([0.0] * 63)
        
        # Mano derecha: 21 puntos × 3 = 63 valores
        if results.right_hand_landmarks:
            for lm in results.right_hand_landmarks.landmark:
                keypoints.extend([lm.x, lm.y, lm.z])
        else:
            keypoints.extend([0.0] * 63)
        
        return keypoints
    
    def close(self):
        if hasattr(self, 'holistic'):
            self.holistic.close()

# Instancia global
_extractor = None

def get_mediapipe_extractor():
    global _extractor
    if _extractor is None:
        _extractor = MediaPipeExtractor()
    return _extractor