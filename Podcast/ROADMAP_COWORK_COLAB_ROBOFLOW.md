# Roadmap Celestials para Cowork, Colab y Roboflow

## Objetivo

Llevar el pipeline de `Celestials` a un estado reproducible donde:

- los textos y audios estén corregidos
- los crops se vean más cercanos y consistentes
- el render de `LivePortrait` pueda correrse en `Colab`
- las tres escenas queden listas para composición final

## Estado actual

### Ya resuelto

- Corrección de nombre `Serrafin` -> `Serratín`
- Regeneración de textos fuente
- Regeneración de `manifest` y `liveportrait_job.json`
- Runner de `LivePortrait` con remux de audio
- Carga local de variables desde `Podcast/.env`

### Pendiente

- Conseguir `voice_id` reales de ElevenLabs
- Regenerar MP3 definitivos
- Validar GPU estable para `LivePortrait`
- Mejorar calidad visual de los crops
- Renderizar las 3 escenas finales

## Fase 1: Cerrar audio y assets base

### Objetivo

Dejar los assets correctos antes de movernos a calidad visual y render en nube.

### Tareas para cowork

- Conseguir los `voice_id` reales:
  - `FER_VOICE_ID`
  - `RUFIS_VOICE_ID`
  - `SERRATIN_VOICE_ID`
- Regenerar los MP3 con los textos corregidos
- Verificar que el `manifest` ya no tenga `audio_pending: true`

### Entregables

- 3 archivos `.mp3` correctos
- `manifest` con `audio_file` por escena
- Duración confirmada de cada audio

### Criterio de salida

Cada escena debe tener:

- `image_file`
- `audio_file`
- `voice_id`

## Fase 2: Baseline visual

### Objetivo

Tener un punto de comparación claro antes de optimizar crops o mover el render a `Colab`.

### Tareas para cowork

- Renderizar 1 escena base, idealmente `Fer`
- Guardar preview de video
- Exportar 1 o 2 frames representativos
- Documentar defectos visuales

### Qué evaluar

- distancia del rostro
- encuadre
- rigidez del movimiento
- coherencia del personaje con la imagen original

### Entregables

- 1 video baseline
- 1 carpeta con frames
- 1 lista corta de defectos

## Fase 3: Roboflow para mejorar crops

### Objetivo

Usar `Roboflow` para proponer mejores cajas de recorte y composición.

### Qué sí usar en Roboflow

- detección de cara
- detección de cabeza
- detección de busto superior
- propuesta de bounding boxes estables por personaje

### Qué no pedirle a Roboflow

- lipsync
- animación facial
- reemplazar `LivePortrait`

### Tareas para cowork

- Crear dataset con:
  - imagen grupal original
  - crops actuales
  - frames del baseline
- Etiquetar ejemplos para Fer, Rufis y Serratín
- Probar 2 enfoques:
  - cara cerrada
  - cara + hombros
- Exportar predicciones o cajas sugeridas

### Entregables

- dataset versionado en Roboflow
- cajas sugeridas por personaje
- comparativa entre crop actual y crop sugerido

### Criterio de salida

Elegir nuevas cajas para:

- `crop_box_rel`
- `compose_box_rel`

## Fase 4: Integración de crops mejorados

### Objetivo

Convertir las sugerencias de `Roboflow` en configuración real del pipeline.

### Tareas para cowork

- Actualizar configuración de crops
- Regenerar imágenes por personaje
- Comparar 2 o 3 variantes por escena

### Entregables

- imágenes nuevas por personaje
- tabla comparativa A/B
- decisión final de crop por personaje

## Fase 5: Preparar Colab

### Objetivo

Mover el render pesado a GPU en nube y hacer el flujo repetible.

### Tareas para cowork

- Preparar notebook de `Colab`
- Montar `Google Drive`
- Subir o clonar `LivePortrait`
- Instalar dependencias necesarias
- Organizar inputs y outputs

### Estructura sugerida en Drive

- `/Celestials/input/`
- `/Celestials/output/`
- `/Celestials/notebooks/`

Dentro de `input`:

- source images
- driving video
- audios `.mp3`
- `manifest`
- `liveportrait_job.json`

### Entregables

- notebook ejecutable
- estructura estable en Drive
- 1 prueba funcional con una escena

### Criterio de salida

Se puede correr una escena de principio a fin en `Colab` sin corregir rutas a mano.

## Fase 6: Batch final en Colab

### Objetivo

Renderizar las tres escenas con la configuración final validada.

### Tareas para cowork

- Lanzar las 3 escenas
- Verificar audio final
- Guardar outputs ordenados
- Registrar reintentos y fallos

### Checklist por escena

- video generado
- audio correcto
- nombre correcto `Serratín`
- crop aceptable
- movimiento usable

### Entregables

- 3 MP4 finales por personaje
- tabla de QA
- carpeta final de outputs

## Fase 7: Composición final

### Objetivo

Combinar los tres resultados sobre la imagen original.

### Tareas para cowork

- Usar `build_liveportrait_composite.py`
- Probar composición secuencial y simultánea
- Ajustar `compose_box_rel` si hace falta

### Entregables

- preview compuesta
- video final compuesto
- notas de ajuste fino

## División de trabajo sugerida

### Tú

- aprobar guiones
- aprobar crops
- elegir el mejor driving video
- aprobar versión final

### Cowork

- preparar Roboflow
- preparar Colab
- ejecutar renders
- documentar resultados
- comparar versiones

### Yo

- parchar scripts
- traducir cajas de Roboflow a config
- ajustar pipeline
- resolver bugs técnicos

## Orden recomendado

1. Conseguir `voice_id` reales
2. Regenerar audios
3. Renderizar baseline de una escena
4. Crear dataset en `Roboflow`
5. Elegir crops finales
6. Montar notebook en `Colab`
7. Renderizar 3 escenas
8. Componer video final

## Checklist rápido para compartir con cowork

### Sprint 1

- conseguir `voice_id` reales
- regenerar MP3
- validar `manifest`
- correr 1 render baseline
- documentar defectos

### Sprint 2

- preparar dataset en `Roboflow`
- etiquetar ejemplos
- proponer nuevas cajas
- entregar comparativa A/B

### Sprint 3

- montar notebook en `Colab`
- correr una escena completa
- correr batch de 3 escenas
- dejar outputs en Drive

## Riesgos principales

- `voice_id` inválidos bloquean TTS
- GPU local sigue inestable
- dataset pequeño en `Roboflow` da cajas inconsistentes
- driving video inadecuado limita el resultado aunque el crop mejore

## Definición de avance real

Solo cuenta como avance si produce al menos uno de estos resultados:

- MP3 nuevo usable
- render mejor que el baseline
- notebook de `Colab` reproducible
- crops finales aprobados
- tres escenas completas renderizadas
