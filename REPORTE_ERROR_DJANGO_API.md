# 🐛 Reporte de Error - Django API (Render)

**Fecha:** 2 de Diciembre, 2025
**Servidor:** https://django-rest-framework-uc05.onrender.com
**Estado:** ❌ Internal Server Error (500) en todos los endpoints

---

## 📊 Síntomas del Problema

### 1. Error General
- **Código HTTP:** 500 Internal Server Error
- **Afecta a:** TODOS los endpoints (root `/`, health `/api/health/`, predict `/api/predict/`)
- **Respuesta:** HTML genérico sin detalles del error

```html
<html>
  <head>
    <title>Internal Server Error</title>
  </head>
  <body>
    <h1><p>Internal Server Error</p></h1>
  </body>
</html>
```

### 2. Endpoints Probados (Todos fallan)

#### ❌ GET `/` (Root)
```bash
curl https://django-rest-framework-uc05.onrender.com/
# Response: 500 Internal Server Error
```

#### ❌ GET `/api/health/`
```bash
curl https://django-rest-framework-uc05.onrender.com/api/health/
# Response: 500 Internal Server Error
```

#### ❌ POST `/api/predict/`
```bash
curl -X POST https://django-rest-framework-uc05.onrender.com/api/predict/ \
  -H "Content-Type: application/json" \
  -d '{"landmarks": [0.5, 0.5, 0.5, ...]}'
# Response: 500 Internal Server Error
```

---

## 🔍 Información Técnica

### Request Headers (lo que la app envía)
```
POST /api/predict/ HTTP/1.1
Host: django-rest-framework-uc05.onrender.com
Content-Type: application/json
User-Agent: Dart/3.9 (dart:io)
```

### Request Body Format
```json
{
  "landmarks": [
    0.123, 0.456, 0.789,
    // ... total 243 valores (double)
    // Representa 81 landmarks × 3 coordenadas (x, y, z)
  ]
}
```

### Response Headers
```
HTTP/1.1 500 Internal Server Error
Date: Tue, 02 Dec 2025 16:47:33 GMT
Content-Type: text/html
Transfer-Encoding: chunked
Connection: keep-alive
CF-RAY: 9a7c4e88d8fc4690-DFW
rndr-id: 3ad98a04-4d4f-4b99
vary: Accept-Encoding
x-render-origin-server: Render
cf-cache-status: DYNAMIC
Server: cloudflare
```

### IP del Servidor
- **IPv4:** 216.24.57.251, 216.24.57.7
- **Proveedor:** Render (Cloudflare proxy)

---

## 🧪 Comportamiento Observado desde la App

### Logs de la Aplicación Flutter (celular Android)
```
I/flutter: 📤 Enviando imagen a MediaPipe server...
I/flutter: ✅ Landmarks extraídos: 243 valores
I/flutter:    Detecciones: {face: true, left_hand: false, pose: true, right_hand: true}

// Landmarks se envían correctamente al Django API pero...

I/flutter: ❌ Error en Django API: 500 - <html>
I/flutter:   <head>
I/flutter:     <title>Internal Server Error</title>
I/flutter:   </head>
I/flutter:   <body>
I/flutter:     <h1><p>Internal Server Error</p></h1>
I/flutter:   </body>
I/flutter: </html>
I/flutter: ! No se pudo conectar con MediaPipe server
```

### Timeline del Error
1. **MediaPipe (local) ✅ ÉXITO** - Extrae 243 landmarks correctamente
2. **Envío a Django API** - POST con JSON válido
3. **Django API ❌ FALLA** - 500 Internal Server Error
4. **Resultado** - No se puede clasificar el gesto

---

## 💡 Posibles Causas

Basándome en errores 500 comunes en Django desplegado en Render:

### 1. **Error de Configuración (Más Probable)**
- ❌ Variables de entorno faltantes o incorrectas
- ❌ `DEBUG=True` en producción (puede ocultar errores)
- ❌ `ALLOWED_HOSTS` no incluye el dominio de Render
- ❌ Archivos estáticos mal configurados

### 2. **Dependencias Faltantes**
- ❌ TensorFlow/Keras no instalado correctamente
- ❌ Modelo `.h5` o `.keras` no encontrado
- ❌ `label_encoder.pkl` no presente o corrupto

### 3. **Error en el Código**
- ❌ Exception no capturada en las views
- ❌ Serializer con validación que falla
- ❌ Formato de datos esperado diferente

### 4. **Problema de Base de Datos**
- ❌ Migraciones no ejecutadas
- ❌ Conexión a DB fallando
- ❌ Timeout en consultas

### 5. **Límites de Render (Free Tier)**
- ❌ Memoria insuficiente (TensorFlow requiere mucha RAM)
- ❌ Disco lleno
- ❌ Cold start muy largo (>30 seg)

---

## 🛠️ Pasos para Depurar

### 1. Revisar Logs de Render
```bash
# En el dashboard de Render, ir a:
# Your Service > Logs
# Buscar el stack trace completo del error 500
```

### 2. Verificar Variables de Entorno
```python
# En settings.py, verificar:
DEBUG = False  # Debe ser False en producción
ALLOWED_HOSTS = [
    'django-rest-framework-uc05.onrender.com',
    '.onrender.com',
]

# Verificar que existan estas variables:
SECRET_KEY = os.environ.get('SECRET_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL')  # Si usa DB
```

### 3. Probar el Modelo Localmente
```python
# Verificar que el modelo se pueda cargar
import pickle
import tensorflow as tf

# Cargar label encoder
with open('label_encoder.pkl', 'rb') as f:
    label_encoder = pickle.load(f)
    print(f"Clases: {label_encoder.classes_}")

# Cargar modelo TensorFlow
model = tf.keras.models.load_model('modelo.h5')  # o .keras
print(f"Input shape: {model.input_shape}")
print(f"Output shape: {model.output_shape}")
```

### 4. Verificar Endpoint de Predicción
```python
# En views.py, agregar logging:
import logging
logger = logging.getLogger(__name__)

@api_view(['POST'])
def predict(request):
    try:
        logger.info(f"Request data: {request.data}")
        landmarks = request.data.get('landmarks', [])
        logger.info(f"Landmarks length: {len(landmarks)}")

        # ... resto del código ...

    except Exception as e:
        logger.error(f"Error en predicción: {str(e)}", exc_info=True)
        return Response(
            {"error": str(e)},
            status=500
        )
```

### 5. Verificar requirements.txt
```txt
# Asegurarse de que incluya:
Django>=4.0
djangorestframework>=3.14
tensorflow>=2.10
numpy>=1.24
scikit-learn>=1.2
django-cors-headers>=3.13
gunicorn>=20.1
```

### 6. Verificar build command en Render
```bash
# Debería ser algo como:
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
```

---

## 📋 Información Adicional

### Formato de Datos que Envía la App
```json
{
  "landmarks": [
    // 243 valores double (81 landmarks × 3 coords)
    // Pose: 33 landmarks (índices 0-98)
    // Face: 6 landmarks (índices 99-116)
    // Left Hand: 21 landmarks (índices 117-179)
    // Right Hand: 21 landmarks (índices 180-242)
  ]
}
```

### Formato de Respuesta Esperado
```json
// Cuando está esperando más frames:
{
  "estado": "esperando 60 frames más"
}

// Cuando tiene predicción:
{
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

## 🚨 Urgencia

**CRÍTICA** - El sistema de reconocimiento de gestos está completamente inoperativo.

**Impacto:**
- ❌ Usuarios no pueden usar la funcionalidad de reconocimiento en tiempo real
- ✅ MediaPipe funciona correctamente (extracción de landmarks)
- ✅ La app móvil funciona correctamente
- ❌ Solo falla la clasificación en el Django API

---

## 📞 Información de Contacto

**Reportado por:** Usuario de Inclusign
**Cliente:** Aplicación Flutter móvil
**Versión:** Flutter 3.35.7 / Dart 3.9.2
**Dispositivo de Prueba:** Redmi Note 9 Pro (Android 10)

---

## ✅ Checklist para el Desarrollador

- [ ] Revisar logs completos en Render dashboard
- [ ] Verificar ALLOWED_HOSTS incluye dominio de Render
- [ ] Confirmar que modelo .h5/.keras está presente
- [ ] Confirmar que label_encoder.pkl está presente
- [ ] Verificar memoria disponible (TensorFlow requiere ~2GB RAM)
- [ ] Probar endpoint localmente primero
- [ ] Agregar logging detallado en el endpoint /api/predict/
- [ ] Verificar que todas las dependencias estén instaladas
- [ ] Considerar DEBUG=True temporalmente para ver el error completo
- [ ] Implementar endpoint /api/health/ que retorne 200 OK

---

## 📎 Archivos Adjuntos

Ver también:
- Logs completos de la app: En consola Flutter
- Screenshots: (si tienes capturas de pantalla)
- Request/Response examples: Ver sección "Información Técnica" arriba
