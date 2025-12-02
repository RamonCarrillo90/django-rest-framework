# Guía de Deployment - API Django REST Framework para Flutter

## Cambios Realizados

### 1. Configuración de Seguridad
- ✅ Variables de entorno para SECRET_KEY, DEBUG y ALLOWED_HOSTS
- ✅ Configuración de CORS para permitir peticiones desde Flutter
- ✅ Desactivación de CSRF para endpoints de API
- ✅ Configuración de REST Framework para aplicaciones móviles

### 2. Archivos de Deployment
- ✅ `Procfile` - Configuración para Heroku/Render
- ✅ `runtime.txt` - Versión de Python
- ✅ `.env.example` - Plantilla de variables de entorno
- ✅ `.gitignore` actualizado

### 3. Endpoints Disponibles
- `POST /api/predict/` - Endpoint con MediaPipe (recibe imagen base64 o landmarks)
- `POST /api/predict-frames/` - Endpoint anterior (recibe frames directamente)

## Configuración Local

### 1. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto basado en `.env.example`:

```bash
# Para desarrollo local
SECRET_KEY=tu-clave-secreta-generada
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

Para generar una SECRET_KEY segura:
```python
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

### 3. Migrar Base de Datos
```bash
python manage.py migrate
```

### 4. Crear Superusuario (opcional)
```bash
python manage.py createsuperuser
```

### 5. Recolectar Archivos Estáticos
```bash
python manage.py collectstatic --noinput
```

### 6. Ejecutar Servidor Local
```bash
python manage.py runserver
```

## Deployment en Heroku

### 1. Instalar Heroku CLI
Descarga e instala desde: https://devcenter.heroku.com/articles/heroku-cli

### 2. Login en Heroku
```bash
heroku login
```

### 3. Crear Aplicación
```bash
heroku create tu-app-nombre
```

### 4. Configurar Variables de Entorno
```bash
heroku config:set SECRET_KEY="tu-clave-secreta-generada"
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS="tu-app-nombre.herokuapp.com"
```

### 5. Deploy
```bash
git add .
git commit -m "Configuración para deployment"
git push heroku main
```

### 6. Migrar Base de Datos en Heroku
```bash
heroku run python manage.py migrate
```

### 7. Crear Superusuario en Heroku
```bash
heroku run python manage.py createsuperuser
```

## Deployment en Render

### 1. Conectar Repositorio
- Ve a https://render.com
- Crea una cuenta y conecta tu repositorio de GitHub

### 2. Crear Web Service
- Selecciona "New +" → "Web Service"
- Conecta tu repositorio
- Configura:
  - **Name**: nombre-de-tu-api
  - **Region**: elige la más cercana
  - **Branch**: main
  - **Runtime**: Python 3
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: `gunicorn drf.wsgi:application`

### 3. Configurar Variables de Entorno
En el panel de Render, agrega:
- `SECRET_KEY` = tu-clave-secreta-generada
- `DEBUG` = False
- `ALLOWED_HOSTS` = tu-app.onrender.com
- `PYTHON_VERSION` = 3.11.9

### 4. Deploy
Render automáticamente desplegará tu aplicación al hacer push a main.

## Configuración en Flutter

### 1. Instalar Paquetes
```yaml
dependencies:
  http: ^1.1.0
  flutter_dotenv: ^5.1.0
```

### 2. Configurar URL de la API
Crea un archivo `lib/config/api_config.dart`:

```dart
class ApiConfig {
  // Para desarrollo local
  static const String baseUrlLocal = 'http://localhost:8000';

  // Para producción (reemplaza con tu URL de Heroku/Render)
  static const String baseUrlProduction = 'https://tu-app.herokuapp.com';

  // Usar según el entorno
  static const String baseUrl = baseUrlProduction; // Cambiar según necesites

  // Endpoints
  static const String predictEndpoint = '/api/predict/';
  static const String predictFramesEndpoint = '/api/predict-frames/';
}
```

### 3. Ejemplo de Petición desde Flutter

#### Opción 1: Enviar Imagen en Base64
```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'api_config.dart';

Future<Map<String, dynamic>> sendImageToAPI(String base64Image) async {
  try {
    final response = await http.post(
      Uri.parse('${ApiConfig.baseUrl}${ApiConfig.predictEndpoint}'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'image': base64Image,
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Error: ${response.statusCode}');
    }
  } catch (e) {
    print('Error al enviar imagen: $e');
    rethrow;
  }
}
```

#### Opción 2: Enviar Landmarks Directamente
```dart
Future<Map<String, dynamic>> sendLandmarks(List<double> landmarks) async {
  try {
    final response = await http.post(
      Uri.parse('${ApiConfig.baseUrl}${ApiConfig.predictEndpoint}'),
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'landmarks': landmarks,
      }),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Error: ${response.statusCode}');
    }
  } catch (e) {
    print('Error al enviar landmarks: $e');
    rethrow;
  }
}
```

### 4. Manejo de Respuestas

La API puede devolver diferentes tipos de respuestas:

```dart
// Esperando más frames
{
  "estado": "esperando 50 frames más",
  "frames_actuales": 15,
  "frames_requeridos": 65
}

// Predicción lista
{
  "estado": "prediccion",
  "gesto": "thumbs_up",
  "confianza": 0.95
}

// Error
{
  "error": "Descripción del error"
}
```

## Solución de Problemas

### CORS Errors
Si obtienes errores de CORS desde Flutter:
1. Verifica que `django-cors-headers` esté instalado
2. Verifica que `CORS_ALLOW_ALL_ORIGINS = True` en settings.py
3. Asegúrate de que el middleware de CORS esté en la posición correcta

### CSRF Errors
Los endpoints de la API ya tienen CSRF desactivado. Si aún recibes errores:
1. Verifica que las vistas tengan el decorador `@method_decorator(csrf_exempt, name='dispatch')`
2. Verifica que no estés enviando cookies de sesión

### 500 Internal Server Error
1. Activa DEBUG temporalmente: `heroku config:set DEBUG=True`
2. Revisa los logs: `heroku logs --tail`
3. Verifica que todas las dependencias estén instaladas

### Static Files Not Loading
Si los archivos estáticos no cargan en producción:
```bash
python manage.py collectstatic --noinput
```

## Seguridad en Producción

### Checklist
- [ ] DEBUG=False
- [ ] SECRET_KEY única y segura
- [ ] ALLOWED_HOSTS configurado correctamente
- [ ] CSRF_TRUSTED_ORIGINS configurado
- [ ] Usar HTTPS en producción
- [ ] Configurar base de datos PostgreSQL (no SQLite)
- [ ] Configurar backups de base de datos
- [ ] Implementar rate limiting si es necesario

### Configuración HTTPS
En producción, asegúrate de configurar:
```python
# En settings.py para producción
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

## Monitoreo

### Logs en Heroku
```bash
heroku logs --tail
```

### Logs en Render
Los logs están disponibles en el dashboard de Render.

## Contacto y Soporte

Si encuentras problemas:
1. Revisa los logs del servidor
2. Verifica la configuración de variables de entorno
3. Asegúrate de que todas las dependencias estén instaladas
4. Verifica que la versión de Python sea compatible
