import numpy as np
import pickle
import os
import logging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Buscar modelo .tflite o .keras
MODEL_TFLITE = os.path.join(BASE_DIR, "ml", "modelo.tflite")
MODEL_KERAS = os.path.join(BASE_DIR, "ml", "best_model_sin_patron_ceros.keras")
LABEL_ENCODER_PATH = os.path.join(BASE_DIR, "ml", "label_encoder.pkl")
NORMALIZER_PATH = os.path.join(BASE_DIR, "ml", "normalizacion_sin_patron.pkl")


class GesturePredictor:

    def __init__(self):
        self.interpreter = None
        self.model = None
        self.input_details = None
        self.output_details = None
        self.label_encoder = None
        self.normalizer = None
        self.use_tflite = False

        try:
            # Intentar cargar modelo TFLite primero
            if os.path.exists(MODEL_TFLITE):
                logger.info(f"Cargando modelo TFLite desde {MODEL_TFLITE}")
                import tflite_runtime.interpreter as tflite
                self.interpreter = tflite.Interpreter(model_path=MODEL_TFLITE)
                self.interpreter.allocate_tensors()
                self.input_details = self.interpreter.get_input_details()
                self.output_details = self.interpreter.get_output_details()
                self.use_tflite = True
                logger.info("✅ Modelo TFLite cargado exitosamente")

            # Si no existe .tflite, usar .keras
            elif os.path.exists(MODEL_KERAS):
                logger.info(f"Modelo TFLite no encontrado, cargando Keras desde {MODEL_KERAS}")
                import tensorflow as tf
                self.model = tf.keras.models.load_model(MODEL_KERAS)
                self.use_tflite = False
                logger.info("✅ Modelo Keras cargado exitosamente")

            else:
                raise FileNotFoundError(
                    f"No se encontró modelo en {MODEL_TFLITE} ni en {MODEL_KERAS}"
                )

            # Load label encoder
            logger.info(f"Cargando label encoder desde {LABEL_ENCODER_PATH}")
            with open(LABEL_ENCODER_PATH, "rb") as f:
                self.label_encoder = pickle.load(f)
            logger.info(f"✅ Label encoder cargado: {len(self.label_encoder.classes_)} clases")

            # Load normalizer
            logger.info(f"Cargando normalizer desde {NORMALIZER_PATH}")
            with open(NORMALIZER_PATH, "rb") as f:
                self.normalizer = pickle.load(f)
            logger.info("✅ Normalizer cargado exitosamente")

        except Exception as e:
            logger.error(f"❌ Error inicializando GesturePredictor: {e}", exc_info=True)
            raise

    def predict(self, sequence_65_frames):
        """
        sequence_65_frames = lista de 65 frames
        Cada frame debe ser un vector del mismo tamaño que usaste en training.
        """
        try:
            logger.info(f"Prediciendo secuencia de {len(sequence_65_frames)} frames")

            seq = np.array(sequence_65_frames, dtype=np.float32)
            logger.info(f"Shape antes de normalizar: {seq.shape}")

            # Normalizar
            seq_norm = self.normalizer.transform(seq.reshape(65, -1))
            logger.info(f"Shape después de normalizar: {seq_norm.shape}")

            # Expandir a batch de 1
            input_data = np.expand_dims(seq_norm, axis=0).astype(np.float32)
            logger.info(f"Shape input final: {input_data.shape}")

            # Predecir según el tipo de modelo
            if self.use_tflite:
                # TFLite
                self.interpreter.set_tensor(self.input_details[0]["index"], input_data)
                self.interpreter.invoke()
                output_data = self.interpreter.get_tensor(self.output_details[0]["index"])
            else:
                # Keras
                output_data = self.model.predict(input_data, verbose=0)

            # Output es (1, num_classes), aplanar
            probabilities = output_data[0]
            logger.info(f"Probabilidades shape: {probabilities.shape}")

            # Top 3 predicciones
            top_3_indices = np.argsort(probabilities)[-3:][::-1]
            top_3_labels = self.label_encoder.inverse_transform(top_3_indices)
            top_3_probs = probabilities[top_3_indices]

            top_3 = [
                {
                    "gesto": label,
                    "probabilidad": float(prob)
                }
                for label, prob in zip(top_3_labels, top_3_probs)
            ]

            # Mejor predicción
            pred_index = np.argmax(probabilities)
            pred_label = self.label_encoder.inverse_transform([pred_index])[0]
            confidence = float(np.max(probabilities))

            logger.info(f"✅ Predicción: {pred_label} (confianza: {confidence:.2f})")

            return {
                "gesto": pred_label,
                "confianza": confidence,
                "top_3": top_3
            }

        except Exception as e:
            logger.error(f"❌ Error en predicción: {e}", exc_info=True)
            raise