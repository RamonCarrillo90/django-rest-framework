import numpy as np
import tflite_runtime.interpreter as tflite  # ✅ Cambiar esta línea
import pickle
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "ml", "modelo.tflite")
LABEL_ENCODER_PATH = os.path.join(BASE_DIR, "ml", "label_encoder.pkl")
NORMALIZER_PATH = os.path.join(BASE_DIR, "ml", "normalizacion_sin_patron.pkl")


class GesturePredictor:

    def __init__(self):
        # ✅ Usar tflite.Interpreter en lugar de tf.lite.Interpreter
        self.interpreter = tflite.Interpreter(model_path=MODEL_PATH)
        self.interpreter.allocate_tensors()

        # Input / output details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # Load label encoder
        with open(LABEL_ENCODER_PATH, "rb") as f:
            self.label_encoder = pickle.load(f)

        # Load normalizer
        with open(NORMALIZER_PATH, "rb") as f:
            self.normalizer = pickle.load(f)

    def predict(self, sequence_65_frames):
        """
        sequence_65_frames = lista de 65 frames
        Cada frame debe ser un vector del mismo tamaño que usaste en training.
        """

        seq = np.array(sequence_65_frames, dtype=np.float32)

        # Normalizar
        seq_norm = self.normalizer.transform(seq.reshape(65, -1))

        # Expandir a batch de 1
        input_data = np.expand_dims(seq_norm, axis=0).astype(np.float32)

        # Pass input to interpreter
        self.interpreter.set_tensor(self.input_details[0]["index"], input_data)
        self.interpreter.invoke()

        # Output
        output_data = self.interpreter.get_tensor(self.output_details[0]["index"])
        pred_index = np.argmax(output_data)

        # Convert to label name
        pred_label = self.label_encoder.inverse_transform([pred_index])[0]

        return {
            "prediction": pred_label,
            "confidence": float(np.max(output_data))
        }