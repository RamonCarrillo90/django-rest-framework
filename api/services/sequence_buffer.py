from collections import deque

# Buffer global que guarda los últimos 65 frames
sequence_buffer = deque(maxlen=65)

def add_landmarks(landmarks):
    """Agrega un frame de landmarks al buffer"""
    sequence_buffer.append(landmarks)

def get_sequence():
    """Retorna la secuencia completa si hay 65 frames, None si no"""
    if len(sequence_buffer) < 65:
        return None
    return list(sequence_buffer)

def get_buffer_size():
    """Retorna el tamaño actual del buffer"""
    return len(sequence_buffer)

def clear_buffer():
    """Limpia el buffer (útil para resetear)"""
    sequence_buffer.clear()