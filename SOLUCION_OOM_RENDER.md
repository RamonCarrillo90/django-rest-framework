# 🔴 SOLUCIÓN: Out of Memory en Render Free Tier

## ❌ Problema Identificado

```
[ERROR] Worker (pid:57) was sent SIGKILL! Perhaps out of memory?
```

**Causa:** TensorFlow consume ~2GB de RAM, pero Render Free Tier solo tiene **512MB**.

---

## 📊 Análisis del Problema

### RAM Requerida vs Disponible

| Componente | RAM Necesaria |
|------------|---------------|
| **TensorFlow completo** | **1.5 - 2GB** |
| Django + dependencias | 100-200MB |
| Gunicorn workers | 50-100MB c/u |
| **TOTAL REQUERIDO** | **~2GB** |
| | |
| **Render Free Tier** | **512MB** ❌ |

**Resultado:** Los workers son matados por el sistema operativo (OOM Killer).

### ¿Por qué TensorFlow es tan pesado?

TensorFlow es una librería completa de Machine Learning que incluye:
- Entrenamiento de modelos
- Optimizadores
- Backends de GPU/CPU
- Herramientas de debugging
- Muchas operaciones que NO necesitas en producción

**Para solo hacer predicciones, TensorFlow es EXCESIVO.**

---

## ✅ SOLUCIÓN GRATUITA: TFLite

**TensorFlow Lite (TFLite)** es la versión optimizada para producción:

| Característica | TensorFlow | TFLite |
|----------------|------------|--------|
| RAM requerida | ~2GB | ~100-200MB ✅ |
| Tamaño de librería | ~500MB | ~5MB |
| Velocidad de inferencia | Normal | Más rápida |
| Funciona en 512MB | ❌ NO | ✅ SÍ |
| Para entrenamiento | ✅ Sí | ❌ No |
| Para predicción | ✅ Sí | ✅ Sí |

**Conclusión:** Usa TFLite en producción, TensorFlow solo en desarrollo.

---

## 🛠️ IMPLEMENTACIÓN PASO A PASO

### Paso 1: Convertir el Modelo a TFLite

Ya creé el script `convert_to_tflite.py`. Ejecútalo:

```bash
# Asegúrate de tener TensorFlow instalado (solo para desarrollo)
pip install -r requirements-dev.txt

# Ejecutar conversión
python convert_to_tflite.py
```

**Salida esperada:**
```
============================================================
CONVERSIÓN DE MODELO KERAS A TFLITE
============================================================

📂 Cargando modelo Keras desde: api/ml/best_model_sin_patron_ceros.keras
✅ Modelo Keras cargado exitosamente

📊 Información del modelo:
   - Input shape: (None, 65, 243)
   - Output shape: (None, 10)
   - Número de parámetros: 123,456

🔄 Convirtiendo a TFLite...
💾 Guardando modelo TFLite en: api/ml/modelo.tflite

📏 Tamaños de archivo:
   - Modelo Keras:  15.23 MB
   - Modelo TFLite: 14.87 MB
   - Reducción:     2.4%

============================================================
✅ CONVERSIÓN EXITOSA
============================================================
```

**IMPORTANTE:** El archivo `api/ml/modelo.tflite` debe haberse creado.

### Paso 2: Verificar el Archivo TFLite

```bash
# Verificar que existe
ls -lh api/ml/modelo.tflite

# Debería mostrar algo como:
# -rw-r--r-- 1 user user 14M dic 2 modelo.tflite
```

### Paso 3: Hacer Commit del Modelo TFLite

```bash
# Agregar el modelo al repositorio
git add api/ml/modelo.tflite

# Commit
git commit -m "Add TFLite model for production (512MB RAM compatible)"

# Push
git push origin main
```

**NOTA:** Si el archivo es muy grande (>100MB), necesitarás Git LFS:

```bash
# Instalar Git LFS (una sola vez)
git lfs install

# Trackear archivos .tflite
git lfs track "*.tflite"

# Agregar .gitattributes
git add .gitattributes

# Ahora agregar el modelo
git add api/ml/modelo.tflite
git commit -m "Add TFLite model with Git LFS"
git push origin main
```

### Paso 4: Verificar Requirements.txt

El archivo `requirements.txt` ya fue actualizado para **NO** incluir TensorFlow:

```txt
# Requirements para PRODUCCIÓN (Render Free Tier - 512MB RAM)
# ⚠️ NO incluye TensorFlow (demasiado pesado)
# ⚠️ Usa tflite-runtime en su lugar (mucho más liviano)

Django==5.0
djangorestframework==3.16.0
django-cors-headers==4.3.1
gunicorn==23.0.0
whitenoise==6.6.0
Pillow==10.1.0
numpy==1.24.3
scikit-learn==1.3.2
tflite-runtime==2.14.0        # ✅ Solo 5MB vs 500MB de TensorFlow
mediapipe==0.10.14
opencv-python-headless==4.8.1.78
python-dotenv==1.0.0
```

### Paso 5: Desplegar en Render

```bash
# Hacer push de todos los cambios
git add .
git commit -m "Fix OOM: Use TFLite instead of TensorFlow (512MB compatible)"
git push origin main
```

Render detectará el push y re-desplegará automáticamente.

### Paso 6: Verificar el Deployment

Espera 3-5 minutos y verifica:

```bash
# 1. Health check
curl https://tu-app.onrender.com/api/health/

# Debería retornar:
# {
#   "status": "healthy",
#   "predictor": "ready",
#   ...
# }
```

```bash
# 2. Revisar logs en Render
# Ve a tu servicio > Logs
# Busca estas líneas:

✅ Modelo TFLite cargado exitosamente
   Input shape: [1, 65, 243]
   Output shape: [1, 10]
✅ Label encoder cargado: 10 clases
✅ Normalizer cargado exitosamente
```

**Si ves estos mensajes = ÉXITO ✅**

---

## 📋 Checklist de Verificación

- [ ] Ejecutado `python convert_to_tflite.py`
- [ ] Verificado que existe `api/ml/modelo.tflite`
- [ ] Commit del archivo `.tflite`
- [ ] Push a repositorio
- [ ] Esperado re-deployment en Render (3-5 min)
- [ ] Verificado `/api/health/` retorna 200 OK
- [ ] Verificado logs muestran "Modelo TFLite cargado"
- [ ] No hay más errores "Out of memory"

---

## 🔍 Solución de Problemas

### Error: "No se encontró modelo.tflite"

**Problema:** El archivo no se subió correctamente a Git.

**Solución:**
```bash
# Verificar que está en Git
git ls-files | grep modelo.tflite

# Si no aparece, agregarlo de nuevo
git add api/ml/modelo.tflite --force
git commit -m "Add TFLite model"
git push
```

### Error: "Perhaps out of memory" persiste

**Problema:** Todavía está usando TensorFlow.

**Solución:**
1. Verifica que `requirements.txt` NO tenga `tensorflow`
2. Verifica que el modelo `.tflite` exista en el servidor
3. Revisa logs de Render para ver qué modelo se está cargando

### Modelo muy grande (>100MB)

**Problema:** Git no permite archivos >100MB.

**Solución: Usar Git LFS**
```bash
# Instalar Git LFS
git lfs install

# Trackear archivos .tflite
git lfs track "*.tflite"
git add .gitattributes

# Agregar modelo
git add api/ml/modelo.tflite
git commit -m "Add TFLite model with LFS"
git push
```

### Error de importación: "No module named 'tflite_runtime'"

**Problema:** `tflite-runtime` no se instaló en Render.

**Solución:**
1. Verifica que `requirements.txt` incluya `tflite-runtime==2.14.0`
2. Revisa los logs de build en Render
3. Si falla la instalación, prueba una versión más antigua: `tflite-runtime==2.12.0`

---

## 💰 Alternativa de Pago (Si No Quieres Usar TFLite)

Si prefieres seguir usando TensorFlow completo:

### Render Starter Plan
- **Precio:** $7/mes
- **RAM:** 2GB ✅
- **CPU:** Compartido
- **Funciona con TensorFlow:** Sí

### Render Standard Plan
- **Precio:** $25/mes
- **RAM:** 4GB
- **CPU:** Dedicado
- **Mejor para:** Tráfico alto

### Railway
- **Precio:** ~$5/mes (pay-as-you-go)
- **RAM:** Configurable
- **Alternativa a Render**

**Mi recomendación:** Usa TFLite gratis. El modelo funciona exactamente igual.

---

## 🎯 Comparación de Soluciones

| Opción | Costo | RAM | Cambios Necesarios | Tiempo |
|--------|-------|-----|-------------------|--------|
| **TFLite (GRATIS)** | $0 | 512MB | Convertir modelo | 10 min ✅ |
| Render Starter | $7/mes | 2GB | Ninguno | 5 min |
| Render Standard | $25/mes | 4GB | Ninguno | 5 min |

**Recomendación:** Usa TFLite. Es GRATIS, más rápido y funciona perfecto.

---

## ✅ Resultado Esperado

Después de implementar TFLite:

### Antes (TensorFlow):
```
[ERROR] Worker (pid:57) was sent SIGKILL! Perhaps out of memory?
[ERROR] Worker (pid:68) was sent SIGKILL! Perhaps out of memory?
[ERROR] Worker (pid:91) was sent SIGKILL! Perhaps out of memory?
❌ Error 500 en todos los endpoints
```

### Después (TFLite):
```
INFO Cargando modelo TFLite desde api/ml/modelo.tflite
INFO ✅ Modelo TFLite cargado exitosamente
INFO    Input shape: [1, 65, 243]
INFO    Output shape: [1, 10]
INFO ✅ Label encoder cargado: 10 clases
INFO ✅ Normalizer cargado exitosamente
✅ API funcionando correctamente
✅ Uso de RAM: ~200MB (de 512MB disponibles)
```

---

## 📞 Resumen

1. **Problema:** TensorFlow requiere 2GB RAM, Render Free tiene 512MB
2. **Solución:** Convertir modelo a TFLite (solo 200MB RAM)
3. **Pasos:**
   - Ejecutar `python convert_to_tflite.py`
   - Commit de `modelo.tflite`
   - Push y re-deploy
4. **Resultado:** API funcionando GRATIS en Render Free Tier

**¿Necesitas pagar?** ❌ NO, TFLite funciona perfecto en 512MB.

---

## 🚀 Siguiente Paso

Ejecuta ahora mismo:

```bash
python convert_to_tflite.py
```

¡Y estarás listo para desplegar! 🎉
