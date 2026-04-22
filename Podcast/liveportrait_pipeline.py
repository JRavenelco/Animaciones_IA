import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SCENES_DIR = BASE_DIR / "_generated_assets" / "celestials_scenes"
DEFAULT_MANIFEST = SCENES_DIR / "club_celestials_escenas_manifest.json"
DEFAULT_OUTPUT = SCENES_DIR / "liveportrait_job.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--default-driving")
    return parser.parse_args()


def load_manifest(path: Path) -> dict:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"No encontré el manifest: {resolved}")
    return json.loads(resolved.read_text(encoding="utf-8"))


def resolve_driving_input(scene: dict, default_driving: str | None) -> str:
    for key in ("driving_video", "driving_template", "driving_pkl", "driving_file"):
        value = scene.get(key)
        if value:
            return value
    if default_driving:
        return default_driving
    audio_file = scene.get("audio_file")
    if audio_file:
        raise RuntimeError(
            f"La escena '{scene.get('scene')}' solo tiene audio ({audio_file}), pero el LivePortrait oficial requiere driving video o template .pkl."
        )
    raise RuntimeError(
        f"La escena '{scene.get('scene')}' no tiene driving_video ni driving_template compatibles con LivePortrait."
    )


def build_liveportrait_job(manifest: dict, default_driving: str | None) -> dict:
    scenes = manifest.get("scenes") or []
    if not scenes:
        raise RuntimeError("El manifest no contiene escenas")
    jobs = []
    for scene in scenes:
        image_file = scene.get("image_file")
        audio_file = scene.get("audio_file")
        if not image_file:
            raise RuntimeError(f"Faltan archivos para LivePortrait en escena: {scene}")
        driving_file = resolve_driving_input(scene, default_driving)
        jobs.append(
            {
                "scene": scene.get("scene"),
                "label": scene.get("label"),
                "source_image": image_file,
                "driving": driving_file,
                "speech_audio": audio_file,
                "compose_box_rel": scene.get("compose_box_rel"),
                "crop_box_rel": scene.get("crop_box_rel"),
                "expected_output_video": str((SCENES_DIR / scene.get("scene") / f"{manifest.get('title')}_{scene.get('scene')}_liveportrait.mp4").resolve()),
            }
        )
    return {
        "title": manifest.get("title"),
        "background_image": manifest.get("image"),
        "generator": "LivePortrait",
        "notes": [
            "Genera un video por personaje en LivePortrait usando source_image + driving video o template .pkl.",
            "Si speech_audio está presente, se puede remuxar al video final del personaje después de inference.py.",
            "Luego recompón los tres videos sobre la imagen original respetando compose_box_rel.",
            "Esta estrategia mantiene a los tres juntos como en la imagen base."
        ],
        "jobs": jobs,
    }


def print_next_steps(job_data: dict, output_path: Path) -> None:
    print(f"Plan de trabajo LivePortrait guardado en: {output_path}")
    print("Siguiente flujo recomendado:")
    print("1. Ejecuta LivePortrait una vez por cada entrada de jobs.")
    print("2. Guarda cada video generado en expected_output_video.")
    print("3. Luego usa un compositor final para poner los tres videos sobre background_image.")
    print(f"Escenas listas para LivePortrait: {len(job_data.get('jobs', []))}")


def main() -> int:
    args = parse_args()
    manifest = load_manifest(Path(args.manifest))
    job_data = build_liveportrait_job(manifest, args.default_driving)
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(job_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print_next_steps(job_data, output_path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
