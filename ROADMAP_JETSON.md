# Roadmap Jetson – Proyecto Animaciones_IA / Club Celestials

## Objetivo

Continuar el proyecto de animación de personajes con LivePortrait en una Jetson (Nano, Xavier NX, Orin, etc.) usando GPU local ARM.

## Hardware recomendado

- Jetson Orin o Xavier NX (mínimo 8 GB RAM)
- Jetson Nano (modo degradado con menor resolución/FPS)
- microSD o SSD NVMe con al menos 40 GB libres
- Acceso SSH o pantalla conectada

## Clonar el proyecto

```bash
git clone https://github.com/JRavenelco/Animaciones_IA.git
cd Animaciones_IA
```

## Estructura del proyecto

```
Animaciones_IA/
├── Podcast/                        # Scripts de Python del proyecto Celestials
│   ├── prepare_celestials_scenes.py
│   ├── run_liveportrait_jobs.py
│   ├── generate_multivoice_celestials_audio.py
│   ├── liveportrait_pipeline.py
│   ├── build_liveportrait_composite.py
│   ├── podcast_env.py
│   ├── club_celestials_*.txt       # Diálogos por personaje
│   ├── .env.example                # Plantilla de variables de entorno
│   └── requirements.txt
├── patches/liveportrait/           # Parches aplicados a LivePortrait
│   ├── human_landmark_runner.py
│   ├── live_portrait_pipeline.py
│   └── cropper.py
└── ROADMAP_JETSON.md               # Este archivo
```

## Paso 1: Instalar LivePortrait en la Jetson

```bash
# Clonar LivePortrait oficial
git clone https://github.com/KwaiVGI/LivePortrait.git
cd LivePortrait

# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar PyTorch para Jetson (JetPack 5.x / 6.x)
# Consultar: https://developer.nvidia.com/embedded/pytorch
# Ejemplo para JetPack 5.1.x:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Instalar dependencias base de LivePortrait
pip install -r requirements_base.txt
pip install -r requirements.txt

# Instalar onnxruntime-gpu compatible con Jetson
# Para JetPack 5.x usar onnxruntime-gpu wheel de NVIDIA:
# https://elinux.org/Jetson_Zoo#ONNX_Runtime
```

## Paso 2: Aplicar los parches al LivePortrait clonado

Desde la raíz de Animaciones_IA:

```bash
cp patches/liveportrait/human_landmark_runner.py  LivePortrait/src/utils/human_landmark_runner.py
cp patches/liveportrait/live_portrait_pipeline.py  LivePortrait/src/live_portrait_pipeline.py
cp patches/liveportrait/cropper.py                 LivePortrait/src/utils/cropper.py
```

## Paso 3: Descargar modelos preentrenados

```bash
cd LivePortrait

# Opción A: huggingface-cli
pip install huggingface_hub
huggingface-cli download KwaiVGI/LivePortrait --local-dir pretrained_weights --exclude "*.git*"

# Opción B: script oficial
python tools/download_models.py
```

## Paso 4: Configurar variables de entorno

Crea el archivo `.env` en `Podcast/`:

```bash
cp Podcast/.env.example Podcast/.env
# Editar con tus valores reales
nano Podcast/.env
```

Contenido mínimo de `.env`:

```env
ELEVENLABS_API_KEY=tu_api_key_de_elevenlabs
FER_VOICE_ID=cgSgspJ2msm6clMCkdW9
RUFIS_VOICE_ID=IKne3meq5aSn9XLyUdCD
SERRATIN_VOICE_ID=JBFqnCBsd6RMkjVDRZzb
```

## Paso 5: Instalar dependencias de Podcast

```bash
cd Podcast
pip install -r requirements.txt
pip install Pillow requests
```

## Paso 6: Regenerar assets (imágenes y audios)

```bash
cd Podcast
python3 prepare_celestials_scenes.py --image trio_de_amigos.jpg
```

Esto genera:
- imágenes recortadas por personaje
- MP3 de voz con ElevenLabs
- manifest JSON

## Paso 7: Regenerar job de LivePortrait

```bash
python3 liveportrait_pipeline.py --default-driving ../LivePortrait/assets/examples/driving/d0.mp4
```

## Paso 8: Correr LivePortrait en Jetson

```bash
python3 run_liveportrait_jobs.py \
  --liveportrait-root ../LivePortrait \
  --job-json _generated_assets/celestials_scenes/liveportrait_job.json
```

Para forzar CPU si hay problemas con GPU:

```bash
python3 run_liveportrait_jobs.py \
  --liveportrait-root ../LivePortrait \
  --job-json _generated_assets/celestials_scenes/liveportrait_job.json \
  --force-cpu
```

## Paso 9: Componer el video final

```bash
python3 build_liveportrait_composite.py \
  --manifest _generated_assets/celestials_scenes/club_celestials_escenas_manifest.json \
  --output _generated_assets/celestials_scenes/final_composite.mp4
```

## Diferencias Jetson vs Windows

| Aspecto | Windows (desarrollo) | Jetson (producción) |
|---|---|---|
| GPU | NVIDIA RTX (CUDA 12.x) | NVIDIA Tegra (CUDA 11.x/12.x JetPack) |
| onnxruntime | onnxruntime-gpu 1.21.0 | wheel específico de NVIDIA para Jetson |
| torch | 2.3.0+cu121 | versión de JetPack |
| `flag_force_cpu` | Opcional | Solo si hay error de provider |
| Velocidad | ~30-60 FPS | ~5-15 FPS dependiendo del modelo |

## Voces premade sugeridas (ElevenLabs plan free)

| Personaje | Voz sugerida | voice_id |
|---|---|---|
| Fer (diablita, femenino) | Jessica - Playful, Bright, Warm | `cgSgspJ2msm6clMCkdW9` |
| Rufis (angelito, masculino) | Charlie - Deep, Confident, Energetic | `IKne3meq5aSn9XLyUdCD` |
| Serratín (carismático, masculino) | George - Warm, Captivating Storyteller | `JBFqnCBsd6RMkjVDRZzb` |

## Checklist de avance

- [ ] Jetson con JetPack actualizado
- [ ] LivePortrait clonado y parches aplicados
- [ ] Modelos descargados en `pretrained_weights/`
- [ ] `.env` configurado con API keys reales
- [ ] Dependencias instaladas en venv
- [ ] Assets regenerados (imágenes + audios)
- [ ] Job JSON generado
- [ ] 1 escena renderizada como prueba (Fer)
- [ ] 3 escenas renderizadas
- [ ] Video final compuesto

## Notas importantes

- **No subas `.env` a git** — ya está en `.gitignore`
- **Los modelos de LivePortrait** (~5 GB) no están en el repo, descárgalos aparte
- **El driving video** `d0.mp4` necesita copiarse desde el repo oficial de LivePortrait o grabarse propio
- En la Jetson puede ser necesario usar `--flag-half-precision` desactivado (`--no-flag-use-half-precision`) si hay errores de precisión

## Recursos

- LivePortrait oficial: https://github.com/KwaiVGI/LivePortrait
- ElevenLabs API: https://elevenlabs.io/app/developers/api-keys
- ONNX Runtime Jetson: https://elinux.org/Jetson_Zoo#ONNX_Runtime
- PyTorch para Jetson: https://developer.nvidia.com/embedded/pytorch
