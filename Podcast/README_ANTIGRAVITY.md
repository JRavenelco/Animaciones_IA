# Antigravity / LivePortrait Contexto

## Objetivo
Este directorio contiene el flujo de trabajo para generar videos de personajes a partir de una imagen grupal, audios por personaje y renders de talking avatar con LivePortrait.

El objetivo actual es:

- preparar escenas individuales por personaje
- generar o reutilizar audio por personaje
- animar cada personaje con LivePortrait usando `source image` + `driving video` o `template`
- remuxear el audio real del personaje al video renderizado
- recomponer los resultados sobre la imagen original

## Problema clave detectado
LivePortrait no funciona a partir de audio solamente.

Requiere:

- una imagen fuente (`source image`)
- un video de conducción (`driving video`) o un template `.pkl`

Por eso el flujo actual no hace lipsync directo desde MP3. En su lugar:

- usa un `driving video` base para la animación facial/corporal
- genera el video del personaje
- luego pega el audio correcto encima del render final

Esto significa que:

- el movimiento de boca y gestos dependen del `driving video`
- el audio final sí corresponde al personaje
- no hay lipsync fonético perfecto si el driving video no coincide con el discurso

## Archivos principales

### Preparación de escenas
- `prepare_celestials_scenes.py`
  - recorta la imagen grupal en escenas por personaje
  - genera metadata de composición
  - produce assets en `_generated_assets/celestials_scenes/`

### Audio
- `generate_multivoice_celestials_audio.py`
  - genera audio por personaje con ElevenLabs

### Jobs de LivePortrait
- `liveportrait_pipeline.py`
  - construye el JSON de trabajo para LivePortrait
  - registra `source_image`, `driving`, `speech_audio` y `expected_output_video`

### Runner de LivePortrait
- `run_liveportrait_jobs.py`
  - ejecuta `LivePortrait/inference.py` por escena
  - encuentra el MP4 bruto generado por LivePortrait
  - remuxea el MP3 real del personaje al video
  - deja el resultado final en la ruta esperada

### Composición final
- `build_liveportrait_composite.py`
  - recompone los videos individuales sobre la imagen original
  - usa posiciones relativas de composición cuando están disponibles

## Directorios importantes
- `Podcast/_generated_assets/celestials_scenes/`
  - escenas, audios, manifiestos y resultados por personaje

- `LivePortrait/`
  - repositorio de LivePortrait
  - contiene `inference.py`, pesos preentrenados y el `venv`

## Estado técnico actual

### Ya hecho
- se preparó el flujo base para escenas por personaje
- se generó un pipeline de jobs para LivePortrait
- se creó un runner que automatiza la inferencia y remux de audio
- se creó un compositor para reconstruir el video final
- se parchó LivePortrait para propagar `flag_force_cpu` y `device_id` hacia el `Cropper`
- se saneó el entorno de Python del subprocess para evitar contaminación de otras instalaciones
- se ajustó `PATH` para que el subprocess vea DLLs de `torch`
- se limpió `CUDA_PATH` del subprocess para evitar conflictos con CUDA del sistema
- se actualizó `onnxruntime-gpu` para intentar una carga de GPU más limpia en Windows

### Validación lograda
- se logró renderizar al menos una escena real de prueba: `fer`
- el runner fue capaz de:
  - lanzar LivePortrait
  - localizar el MP4 generado
  - remuxear el MP3
  - producir un archivo final utilizable

## Problema funcional actual
El flujo técnico ya funciona bastante mejor, pero se detectó un problema de contenido:

- varios textos fuente fueron editados para usar `Serrafin`
- por eso algunos audios y renders heredaron ese contenido equivocado
- el render puede estar bien técnicamente y aun así estar mal narrativamente

### Implicación
Si el texto fuente está mal, hay que regenerar todo lo derivado:

- texto
- audio
- escenas y manifest
- job JSON de LivePortrait
- renders
- composición final

## Archivos de texto sensibles
Revisar especialmente:

- `club_celestials_fer.txt`
- `club_celestials_rufis.txt`
- `club_celestials_serratin.txt`
- `club_celestials_dialogo.txt`
- `club_celestials_presentacion.txt`

## Flujo recomendado de trabajo

### 1. Corregir el contenido fuente
Asegurarse de que los `.txt` tengan exactamente el diálogo correcto.

### 2. Regenerar audio
Volver a generar los audios si cambiaron los textos.

### 3. Regenerar escenas
Volver a preparar escenas y manifest para que todo quede sincronizado.

### 4. Regenerar jobs de LivePortrait
Actualizar `liveportrait_job.json` con los assets correctos.

### 5. Renderizar escenas
Ejecutar el runner de LivePortrait por escena o para todas.

### 6. Componer el video final
Usar el compositor una vez que los tres renders estén correctos.

## Comandos útiles

### Ejecutar una sola escena
```powershell
py -3.12 c:\Users\jesus\Documents\CEROC\Podcast\run_liveportrait_jobs.py --scene fer
```

### Forzar CPU
```powershell
py -3.12 c:\Users\jesus\Documents\CEROC\Podcast\run_liveportrait_jobs.py --scene fer --force-cpu
```

## Limitaciones actuales
- LivePortrait no hace lipsync desde audio puro en este flujo
- el movimiento depende del `driving video`
- la parte ONNX/CUDA en Windows ha requerido ajustes de entorno
- antes de lanzar las tres escenas finales, conviene confirmar que el contenido textual correcto ya fue regenerado

## Próximo paso recomendado
Antes de renderizar las tres escenas definitivas:

- corregir los textos fuente incorrectos
- regenerar audio y assets derivados
- validar una escena rápida
- luego lanzar las tres escenas
- finalmente componer el video final
