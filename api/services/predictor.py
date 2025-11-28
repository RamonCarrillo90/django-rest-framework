import numpy as np
import tensorflow as tf
import pickle
from pathlib import Path
from .sequence_buffer import get_sequence

BASE = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE / "ml/modelo_gestos.keras"
ENCODER_PATH = BASE / "ml/label_encoder.pkl"
NORM_PATH = BASE / "ml/normalizacion.pkl"
META_PATH = BASE / "ml/metadata.pkl"

model = tf.keras.models.load_model(MODEL_PATH)

with open(ENCODER_PATH, "rb") as f:
    encoder = pickle.load(f)

with open(NORM_PATH, "rb") as f:
    norm = pickle.load(f)

with open(META_PATH, "rb") as f:
    metadata = pickle.load(f)

global_mean = norm["mean"]
global_std = norm["std"]
num_features = norm["num_features"]
classes = metadata["classes"]


def predecir_desde_landmarks():
    seq = get_sequence()
    if seq is None:
        return None  # aún no hay 65 frames

    X = np.array(seq)
    X = (X - global_mean) / global_std
    X = X.reshape(1, 65, num_features)

    pred = model.predict(X, verbose=0)[0]
    top = np.argmax(pred)

    return {
        "gesto": encoder.inverse_transform([top])[0],
        "confianza": float(pred[top]),
        "top_3": [
            {"gesto": classes[i], "prob": float(pred[i])}
            for i in np.argsort(pred)[-3:][::-1]
        ]
    }
