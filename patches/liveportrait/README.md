# LivePortrait Patches

Estos archivos reemplazan los originales del repositorio oficial de LivePortrait.

## Archivos a reemplazar

Después de clonar LivePortrait, copia estos archivos sobre los originales:

```bash
cp patches/liveportrait/human_landmark_runner.py  LivePortrait/src/utils/human_landmark_runner.py
cp patches/liveportrait/live_portrait_pipeline.py  LivePortrait/src/live_portrait_pipeline.py
cp patches/liveportrait/cropper.py                 LivePortrait/src/utils/cropper.py
```

## Qué cambia

- **`human_landmark_runner.py`**: Preload de DLLs CUDA/cuDNN para ONNX Runtime en Windows. Evita el error `LoadLibrary failed with error 126`.
- **`live_portrait_pipeline.py`**: Pasa correctamente `device_id` y `flag_force_cpu` al `Cropper`.
- **`cropper.py`**: Lee `flag_force_cpu` para usar `CPUExecutionProvider` o `CUDAExecutionProvider` según corresponda.

## Versión base

Los parches fueron aplicados sobre:

- LivePortrait commit del repositorio oficial: `KwaiVGI/LivePortrait`
- onnxruntime-gpu: `1.21.0`
- torch: `2.3.0+cu121`
