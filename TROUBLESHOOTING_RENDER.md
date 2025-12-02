# 🔧 Troubleshooting - Django API en Render

## ✅ Problemas Solucionados

Este documento explica los problemas identificados en el reporte de errores y cómo fueron solucionados.

---

## 🐛 Error 500 - Problema Principal RESUELTO

### Problema Identificado
El servidor retornaba error 500 en **TODOS** los endpoints (incluyendo `/`, `/api/health/`, `/api/predict/`) porque:

1. **Modelo no encontrado**: El código buscaba `modelo.tflite` pero el archivo no existía
2. **Carga al iniciar**: El predictor se instanciaba a nivel de módulo, causando que TODO el servidor crasheara si fallaba
3. **Sin logging**: No había información de depuración en los logs
4. **Endpoint health faltante**: No había forma de verificar el estado del servidor

### ✅ Soluciones Implementadas

#### 1. Carga Flexible del Modelo (`api/services/predictor.py`)
```python
# ANTES (❌ Fallaba si modelo.tflite no existía)
MODEL_PATH = os.path.join(BASE_DIR, "ml", "modelo.tflite")
self.interpreter = tflite.Interpreter(model_path=MODEL_PATH)

# DESPUÉS (✅ Intenta TFLite primero, luego Keras)
if os.path.exists(MODEL_TFLITE):
    import tflite_runtime.interpreter as tflite
    self.interpreter = tflite.Interpreter(model_path=MODEL_TFLITE)
    self.use_tflite = True
elif os.path.exists(MODEL_KERAS):
    import tensorflow as tf
    self.model = tf.keras.models.load_model(MODEL_KERAS)
    self.use_tflite = False
```

**Beneficio**: Ahora funciona con archivos `.keras` o `.tflite`

#### 2. Lazy Loading del Predictor (`api/views.py`)
```python
# ANTES (❌ Se instanciaba al importar, crasheaba todo)
predictor = GesturePredictor()

# DESPUÉS (✅ Se carga solo cuando se necesita)
_predictor = None

def get_predictor():
    global _predictor
    if _predictor is None:
        _predictor = GesturePredictor()
    return _predictor
```

**Beneficio**: Si el modelo falla, solo fallan los endpoints de predicción, no todo el servidor

#### 3. Logging Completo
Se agregó logging en:
- `api/services/predictor.py` - Carga del modelo
- `api/views.py` - Procesamiento de requests
- `drf/settings.py` - Configuración de logging

**Beneficio**: Ahora puedes ver exactamente qué está pasando en los logs de Render

#### 4. Endpoint Health Check
```python
GET /api/health/

Response:
{
  "status": "healthy",
  "service": "Django REST Framework - Gesture Recognition API",
  "version": "1.4",
  "predictor": "ready",  // o "not_initialized"
  "buffer_size": 0,
  "endpoints": { ... }
}
```

**Beneficio**: Puedes verificar el estado del servidor sin cargar el modelo

#### 5. Respuesta Mejorada
```python
# ANTES
{
  "prediction": "HOLA",
  "confidence": 0.95
}

# DESPUÉS (incluye top_3 como pedía el cliente)
{
  "estado": "prediccion",
  "gesto": "HOLA",
  "confianza": 0.95,
  "top_3": [
    {"gesto": "HOLA", "probabilidad": 0.95},
    {"gesto": "BUENOS_DIAS", "probabilidad": 0.03},
    {"gesto": "ADIOS", "probabilidad": 0.01}
  ]
}
```

---

## 📋 Checklist de Deployment en Render

### Antes de Desplegar

- [ ] **Verificar archivos del modelo**
  ```bash
  # Uno de estos archivos DEBE existir:
  ls api/ml/modelo.tflite
  # O
  ls api/ml/best_model_sin_patron_ceros.keras
  ```

- [ ] **Verificar archivos auxiliares**
  ```bash
  ls api/ml/label_encoder.pkl
  ls api/ml/normalizacion_sin_patron.pkl
  ```

- [ ] **Crear archivo .tflite (recomendado para producción)**
  ```python
  import tensorflow as tf

  # Cargar modelo Keras
  model = tf.keras.models.load_model('api/ml/best_model_sin_patron_ceros.keras')

  # Convertir a TFLite
  converter = tf.lite.TFLiteConverter.from_keras_model(model)
  tflite_model = converter.convert()

  # Guardar
  with open('api/ml/modelo.tflite', 'wb') as f:
      f.write(tflite_model)

  print("✅ Modelo convertido a TFLite")
  ```

### Configuración en Render

#### Variables de Entorno
```bash
SECRET_KEY=tu-clave-secreta-generada-con-django
DEBUG=False
ALLOWED_HOSTS=tu-app.onrender.com
PYTHON_VERSION=3.11.9
```

#### Build Command
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

#### Start Command
```bash
gunicorn drf.wsgi:application
```

---

## 🔍 Cómo Verificar que Todo Funciona

### 1. Health Check
```bash
curl https://tu-app.onrender.com/api/health/
```

**Respuesta esperada (✅ OK):**
```json
{
  "status": "healthy",
  "predictor": "ready"
}
```

**Respuesta de error (❌ Problema):**
```json
{
  "status": "unhealthy",
  "error": "..."
}
```

### 2. Test de Predicción
```bash
curl -X POST https://tu-app.onrender.com/api/predict/ \
  -H "Content-Type: application/json" \
  -d '{
    "landmarks": [0.5, 0.5, 0.5, ... (243 valores)]
  }'
```

**Primera respuesta (esperando frames):**
```json
{
  "estado": "esperando 64 frames más",
  "frames_actuales": 1,
  "frames_requeridos": 65
}
```

**Después de 65 frames:**
```json
{
  "estado": "prediccion",
  "gesto": "HOLA",
  "confianza": 0.95,
  "top_3": [...]
}
```

---

## 📊 Monitoreo de Logs

### Ver logs en Render
1. Ve a tu servicio en Render
2. Click en "Logs" en el menú izquierdo
3. Busca estos mensajes:

**✅ Inicialización exitosa:**
```
INFO Cargando modelo Keras desde .../best_model_sin_patron_ceros.keras
INFO ✅ Modelo Keras cargado exitosamente
INFO ✅ Label encoder cargado: 10 clases
INFO ✅ Normalizer cargado exitosamente
```

**✅ Requests funcionando:**
```
INFO 📥 POST /api/predict/ - Recibiendo request
INFO 📊 Recibiendo landmarks directamente
INFO ✅ Landmarks recibidos: 243 valores
INFO 📦 Buffer size: 1/65 frames
```

**✅ Predicción exitosa:**
```
INFO 🔮 Iniciando predicción...
INFO Prediciendo secuencia de 65 frames
INFO ✅ Predicción: HOLA (confianza: 0.95)
```

**❌ Errores a buscar:**
```
ERROR ❌ Error inicializando GesturePredictor: [Errno 2] No such file or directory: '...'
ERROR ❌ Error en predicción: ...
```

---

## 🚨 Problemas Comunes

### Error: "No se encontró modelo"
```
FileNotFoundError: No se encontró modelo en .../modelo.tflite ni en .../best_model_sin_patron_ceros.keras
```

**Solución:**
1. Verifica que los archivos del modelo estén en `api/ml/`
2. Asegúrate de que Git LFS esté configurado para archivos grandes
3. O convierte el modelo a `.tflite` antes de deployar

### Error: "Out of Memory"
```
MemoryError: Unable to allocate array
```

**Solución:**
1. Render Free Tier tiene 512MB RAM
2. TensorFlow requiere ~1-2GB
3. **Opciones:**
   - Usar `.tflite` en lugar de `.keras` (más liviano)
   - Upgrade a plan de pago en Render
   - Desplegar en otra plataforma con más RAM

### Error: "Module not found: tensorflow"
```
ModuleNotFoundError: No module named 'tensorflow'
```

**Solución:**
1. Verifica que `requirements.txt` incluya `tensorflow==2.15.0`
2. Revisa los logs del build en Render
3. Si falla la instalación, prueba con versión más antigua: `tensorflow==2.12.0`

### Error 500 en todos los endpoints
```
Internal Server Error en /, /api/health/, /api/predict/
```

**Solución con los cambios actuales:**
- ✅ Ya NO debería pasar (lazy loading previene esto)
- Si pasa, revisa logs: `heroku logs --tail` o logs de Render
- Verifica que las variables de entorno estén configuradas

---

## 🎯 Mejoras de Performance

### 1. Usar TFLite en Producción
TFLite es **10x más liviano** que TensorFlow completo:
- `.keras` + TensorFlow: ~2GB RAM
- `.tflite` + tflite-runtime: ~200MB RAM

### 2. Configurar Timeout
En `gunicorn`, agrega timeout:
```bash
gunicorn drf.wsgi:application --timeout 120
```

### 3. Workers
Para mejor concurrencia:
```bash
gunicorn drf.wsgi:application --workers 2 --threads 2
```

---

## 📞 Próximos Pasos

### Para el Desarrollador Django:
1. Convertir modelo a `.tflite` si aún no lo hiciste
2. Verificar que los archivos `.pkl` y `.keras` estén en `api/ml/`
3. Configurar variables de entorno en Render
4. Desplegar y verificar con `/api/health/`
5. Monitorear logs durante las primeras predicciones

### Para el Desarrollador Flutter:
1. El formato de respuesta cambió - actualiza el parsing:
   ```dart
   // Antes
   final prediction = response['prediction'];
   final confidence = response['confidence'];

   // Ahora
   final gesto = response['gesto'];
   final confianza = response['confianza'];
   final top3 = response['top_3'];  // NUEVO
   ```

2. Usa el endpoint `/api/health/` para verificar conexión antes de enviar frames

---

## ✅ Estado Final

| Problema | Estado | Solución |
|----------|--------|----------|
| Error 500 en todos los endpoints | ✅ RESUELTO | Lazy loading del predictor |
| Modelo .tflite no encontrado | ✅ RESUELTO | Soporte para .keras |
| Sin logging | ✅ RESUELTO | Logging completo |
| Sin endpoint /health/ | ✅ RESUELTO | Endpoint creado |
| Respuesta sin top_3 | ✅ RESUELTO | Incluido en respuesta |
| CSRF errors | ✅ RESUELTO | @csrf_exempt en vistas |
| Variables hardcodeadas | ✅ RESUELTO | Variables de entorno |

---

## 🎉 Resultado Esperado

Después de estas correcciones:
- ✅ `/api/health/` retorna 200 OK
- ✅ `/api/predict/` acepta landmarks y retorna predicciones
- ✅ Los logs muestran información detallada
- ✅ El servidor no crashea si el modelo falla al cargar
- ✅ La app Flutter puede consumir la API correctamente
