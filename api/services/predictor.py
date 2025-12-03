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
            # PRODUCCIÓN: Solo usar TFLite (liviano, ~200MB RAM)
            # NOTA: TensorFlow completo requiere ~2GB RAM y no funciona en Render Free Tier
            if os.path.exists(MODEL_TFLITE):
                logger.info(f"Cargando modelo TFLite desde {MODEL_TFLITE}")
                import tflite_runtime.interpreter as tflite
                self.interpreter = tflite.Interpreter(model_path=MODEL_TFLITE)
                self.interpreter.allocate_tensors()
                self.input_details = self.interpreter.get_input_details()
                self.output_details = self.interpreter.get_output_details()
                self.use_tflite = True
                logger.info("✅ Modelo TFLite cargado exitosamente")
                logger.info(f"   Input shape: {self.input_details[0]['shape']}")
                logger.info(f"   Output shape: {self.output_details[0]['shape']}")

            # DESARROLLO: Fallback a Keras solo si TFLite no existe
            # ADVERTENCIA: Esto NO funcionará en Render Free Tier (512MB RAM)
            elif os.path.exists(MODEL_KERAS):
                logger.warning(f"⚠️  ADVERTENCIA: Usando modelo Keras (requiere ~2GB RAM)")
                logger.warning(f"⚠️  Esto NO funcionará en Render Free Tier (512MB)")
                logger.warning(f"⚠️  Ejecuta 'python convert_to_tflite.py' para crear modelo.tflite")

                try:
                    import tensorflow as tf
                    self.model = tf.keras.models.load_model(MODEL_KERAS)
                    self.use_tflite = False
                    logger.info("✅ Modelo Keras cargado (solo para desarrollo local)")
                except ImportError:
                    raise ImportError(
                        "TensorFlow no está instalado y modelo.tflite no existe.\n"
                        "Para producción: Ejecuta 'python convert_to_tflite.py'\n"
                        "Para desarrollo: Instala con 'pip install -r requirements-dev.txt'"
                    )

            else:
                raise FileNotFoundError(
                    f"❌ No se encontró modelo en {MODEL_TFLITE} ni en {MODEL_KERAS}\n\n"
                    f"SOLUCIÓN:\n"
                    f"1. Asegúrate de que existe: api/ml/best_model_sin_patron_ceros.keras\n"
                    f"2. Ejecuta: python convert_to_tflite.py\n"
                    f"3. Verifica que se creó: api/ml/modelo.tflite\n"
                    f"4. Haz commit: git add api/ml/modelo.tflite\n"
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

            # Normalizar manualmente usando mean y std
            if isinstance(self.normalizer, dict):
                # El normalizer es un diccionario con 'mean' y 'std'
                mean = self.normalizer['mean']
                std = self.normalizer['std']
                seq_reshaped = seq.reshape(65, -1)
                seq_norm = (seq_reshaped - mean) / std
                logger.info(f"Normalización manual con mean={mean:.4f}, std={std:.4f}")
            else:
                # Fallback: usar .transform() si es un objeto sklearn
                seq_norm = self.normalizer.transform(seq.reshape(65, -1))

            logger.info(f"Shape después de normalizar: {seq_norm.shape}")

            # Expandir a batch de 1
            input_data = np.expand_dims(seq_norm, axis=0).astype(np.float32)
            logger.info(f"Shape input antes de ajustar batch: {input_data.shape}")

            # Predecir según el tipo de modelo
            if self.use_tflite:
                # TFLite: Verificar batch size esperado
                expected_batch_size = self.input_details[0]['shape'][0]

                if expected_batch_size > 1 and input_data.shape[0] == 1:
                    # El modelo espera un batch size fijo mayor que 1
                    # Repetir la secuencia para llenar el batch
                    logger.warning(f"⚠️  Modelo espera batch_size={expected_batch_size}, ajustando...")
                    input_data = np.repeat(input_data, expected_batch_size, axis=0)
                    logger.info(f"Shape input después de ajustar batch: {input_data.shape}")

                self.interpreter.set_tensor(self.input_details[0]["index"], input_data)
                self.interpreter.invoke()
                output_data = self.interpreter.get_tensor(self.output_details[0]["index"])

                # Si repetimos la secuencia, tomar solo la primera predicción
                if expected_batch_size > 1:
                    output_data = output_data[0:1]
                    logger.info(f"Tomando primera predicción del batch: {output_data.shape}")
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