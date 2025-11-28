from collections import deque

# Buffer global que guarda los últimos 65 frames
sequence_buffer = deque(maxlen=65)

def add_landmarks(landmarks):
    sequence_buffer.append(landmarks)

def get_sequence():
    if len(sequence_buffer) < 65:
        return None  # no hay suficientes frames
    return list(sequence_buffer)
