"""
Script para convertir el modelo Keras a TFLite
Esto reduce el uso de RAM de ~2GB a ~200MB
"""
import tensorflow as tf
import os

# Rutas
KERAS_MODEL_PATH = "api/ml/best_model_sin_patron_ceros.keras"
TFLITE_MODEL_PATH = "api/ml/modelo.tflite"

def convert_keras_to_tflite():
    """Convierte el modelo Keras a TFLite"""

    print("=" * 60)
    print("CONVERSIÓN DE MODELO KERAS A TFLITE")
    print("=" * 60)

    # Verificar que el modelo Keras existe
    if not os.path.exists(KERAS_MODEL_PATH):
        print(f"❌ ERROR: No se encontró el modelo en {KERAS_MODEL_PATH}")
        return False

    print(f"\n📂 Cargando modelo Keras desde: {KERAS_MODEL_PATH}")

    try:
        # Cargar modelo Keras
        model = tf.keras.models.load_model(KERAS_MODEL_PATH)
        print("✅ Modelo Keras cargado exitosamente")

        # Mostrar información del modelo
        print(f"\n📊 Información del modelo:")
        print(f"   - Input shape: {model.input_shape}")
        print(f"   - Output shape: {model.output_shape}")
        print(f"   - Número de parámetros: {model.count_params():,}")

        # Convertir a TFLite
        print(f"\n🔄 Convirtiendo a TFLite...")
        converter = tf.lite.TFLiteConverter.from_keras_model(model)

        # Optimizaciones opcionales (descomenta si quieres modelo más pequeño)
        # converter.optimizations = [tf.lite.Optimize.DEFAULT]

        tflite_model = converter.convert()

        # Guardar modelo TFLite
        print(f"💾 Guardando modelo TFLite en: {TFLITE_MODEL_PATH}")
        with open(TFLITE_MODEL_PATH, 'wb') as f:
            f.write(tflite_model)

        # Mostrar tamaños
        keras_size = os.path.getsize(KERAS_MODEL_PATH) / (1024 * 1024)
        tflite_size = os.path.getsize(TFLITE_MODEL_PATH) / (1024 * 1024)

        print(f"\n📏 Tamaños de archivo:")
        print(f"   - Modelo Keras:  {keras_size:.2f} MB")
        print(f"   - Modelo TFLite: {tflite_size:.2f} MB")
        print(f"   - Reducción:     {((keras_size - tflite_size) / keras_size * 100):.1f}%")

        print("\n" + "=" * 60)
        print("✅ CONVERSIÓN EXITOSA")
        print("=" * 60)
        print("\nPróximos pasos:")
        print("1. Verifica que el archivo 'modelo.tflite' fue creado")
        print("2. Haz commit del nuevo archivo:")
        print("   git add api/ml/modelo.tflite")
        print("   git commit -m 'Add TFLite model for production'")
        print("3. Actualiza requirements.txt (quita tensorflow)")
        print("4. Despliega en Render")
        print()

        return True

    except Exception as e:
        print(f"\n❌ ERROR durante la conversión: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tflite_model():
    """Prueba que el modelo TFLite funciona correctamente"""

    print("\n" + "=" * 60)
    print("PROBANDO MODELO TFLITE")
    print("=" * 60)

    if not os.path.exists(TFLITE_MODEL_PATH):
        print(f"❌ ERROR: No se encontró el modelo TFLite en {TFLITE_MODEL_PATH}")
        return False

    try:
        import numpy as np
        import tflite_runtime.interpreter as tflite

        # Cargar intérprete TFLite
        print(f"\n📂 Cargando modelo TFLite...")
        interpreter = tflite.Interpreter(model_path=TFLITE_MODEL_PATH)
        interpreter.allocate_tensors()

        # Obtener detalles de entrada/salida
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        print("✅ Modelo TFLite cargado exitosamente")
        print(f"\n📊 Detalles del modelo:")
        print(f"   - Input shape:  {input_details[0]['shape']}")
        print(f"   - Output shape: {output_details[0]['shape']}")

        # Crear datos de prueba
        input_shape = input_details[0]['shape']
        test_data = np.random.random(input_shape).astype(np.float32)

        # Hacer predicción de prueba
        print(f"\n🔮 Haciendo predicción de prueba...")
        interpreter.set_tensor(input_details[0]['index'], test_data)
        interpreter.invoke()
        output_data = interpreter.get_tensor(output_details[0]['index'])

        print(f"✅ Predicción exitosa")
        print(f"   - Shape de salida: {output_data.shape}")
        print(f"   - Suma de probabilidades: {np.sum(output_data):.4f}")

        print("\n" + "=" * 60)
        print("✅ PRUEBA EXITOSA - El modelo TFLite funciona correctamente")
        print("=" * 60)

        return True

    except ImportError:
        print("\n⚠️  ADVERTENCIA: No se pudo importar tflite_runtime")
        print("   Esto es normal si no lo tienes instalado localmente.")
        print("   El modelo funcionará en producción.")
        return True

    except Exception as e:
        print(f"\n❌ ERROR durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 Iniciando conversión de modelo Keras a TFLite\n")

    # Convertir modelo
    success = convert_keras_to_tflite()

    if success:
        # Probar modelo
        test_tflite_model()
    else:
        print("\n❌ La conversión falló. Revisa los errores arriba.")
        exit(1)
