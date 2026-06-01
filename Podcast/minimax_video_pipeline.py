from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import requests

from podcast_env import load_local_env

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
SCENES_DIR = BASE_DIR / "_generated_assets" / "celestials_scenes"
OPENROUTER_DIR = BASE_DIR / "_generated_assets" / "openrouter_scenes"
DEFAULT_MANIFEST = SCENES_DIR / "club_celestials_escenas_manifest.json"
DEFAULT_PLAN = OPENROUTER_DIR / "openrouter_video_job.json"

DEFAULT_REFERENCE_IMAGE_URL = (
    "https://raw.githubusercontent.com/JRavenelco/Animaciones_IA/master/Podcast/trio_de_amigos.jpg"
)

OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"

load_local_env(ROOT_DIR)
load_local_env(BASE_DIR)

SCENE_PROMPTS = {
    "fer": (
        "Use the attached first frame as the exact visual reference. Focus on the center girl, Fer, "
        "the red-haired cute mischievous little devil girl. Keep the same face, hairstyle, horns, outfit, "
        "colors, friendly child-safe cartoon style, and celestial cloud background. She smiles and speaks "
        "to camera with playful warm energy. Gentle blinking, subtle head movement, expressive eyes, natural "
        "mouth movement, hands on hips, no character redesign, no outfit change. [Static shot]"
    ),
    "rufis": (
        "Use the attached first frame as the exact visual reference. Focus on the left boy, Rufis, "
        "the blonde cute joyful little angel with glasses, halo, and wings. Keep the same face, hair, outfit, "
        "colors, friendly child-safe cartoon style, and celestial cloud background. He smiles and speaks "
        "to camera with bright cheerful energy. Gentle blinking, subtle head movement, expressive eyes, natural "
        "mouth movement, small upbeat gesture, no character redesign, no outfit change. [Static shot]"
    ),
    "serratin": (
        "Use the attached first frame as the exact visual reference. Focus on the right boy, Serratín, "
        "the charming celestial angel boy with brown hair, halo, wings, and white outfit. Keep the same face, "
        "outfit, colors, friendly child-safe cartoon style, and celestial cloud background. He smiles and speaks "
        "to camera with warm charismatic energy. Gentle blinking, subtle head movement, expressive eyes, natural "
        "mouth movement, small wave gesture, no character redesign, no outfit change. [Static shot]"
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output", default=str(DEFAULT_PLAN))
    parser.add_argument("--scene", choices=["fer", "rufis", "serratin"])
    parser.add_argument("--model", default=os.getenv("OPENROUTER_VIDEO_MODEL", "minimax/hailuo-2.3"))
    parser.add_argument("--reference-image-url", default=os.getenv("OPENROUTER_REFERENCE_IMAGE_URL", DEFAULT_REFERENCE_IMAGE_URL))
    parser.add_argument("--duration", type=int, default=6)
    parser.add_argument("--resolution", default="1080p", choices=["720p", "1080p"])
    parser.add_argument("--aspect-ratio", default="16:9")
    parser.add_argument("--prompt")
    parser.add_argument("--generate-audio", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--poll-seconds", type=int, default=30)
    parser.add_argument("--timeout-minutes", type=int, default=30)
    return parser.parse_args()


def load_json(path: Path) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"No encontré el archivo: {resolved}")
    return json.loads(resolved.read_text(encoding="utf-8"))


def save_json(data: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def resolve_openrouter_api_key() -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key:
        return api_key
    raise RuntimeError("Falta OPENROUTER_API_KEY en .env, Podcast/.env o variables de entorno.")


def scene_prompt(scene: dict[str, Any], override: str | None) -> str:
    if override:
        return override
    scene_key = scene.get("scene", "")
    label = scene.get("label") or scene_key
    base = SCENE_PROMPTS.get(scene_key, "")
    text_file = scene.get("text_file")
    spoken_text = ""
    if text_file and Path(text_file).exists():
        spoken_text = Path(text_file).read_text(encoding="utf-8").strip()
    if spoken_text:
        return f"{base} The character presents this Spanish Latin American dialogue idea: {spoken_text}"
    return base or f"{label} speaks to camera with friendly Club Celestials energy. Keep the first-frame character consistent. [Static shot]"


def build_plan(manifest: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    title = manifest.get("title") or "club_celestials"
    background_image = manifest.get("image") or str((BASE_DIR / "trio_de_amigos.jpg").resolve())
    jobs = []
    for scene in manifest.get("scenes") or []:
        if args.scene and scene.get("scene") != args.scene:
            continue
        scene_key = scene.get("scene")
        if not scene_key:
            raise RuntimeError(f"Escena incompleta en manifest: {scene}")
        output_dir = OPENROUTER_DIR / scene_key
        jobs.append(
            {
                "scene": scene_key,
                "label": scene.get("label"),
                "reference_image_url": args.reference_image_url,
                "local_source_image": scene.get("image_file"),
                "speech_audio": scene.get("audio_file") or default_scene_audio(scene_key, title),
                "compose_box_rel": scene.get("compose_box_rel"),
                "prompt": scene_prompt(scene, args.prompt),
                "model": args.model,
                "duration": args.duration,
                "resolution": args.resolution,
                "aspect_ratio": args.aspect_ratio,
                "generate_audio": args.generate_audio,
                "expected_output_video": str((output_dir / f"{title}_{scene_key}_openrouter.mp4").resolve()),
            }
        )
    if not jobs:
        raise RuntimeError("No hay escenas OpenRouter para procesar.")
    return {
        "title": title,
        "background_image": background_image,
        "generator": "OpenRouter Video Generation",
        "mode": "image_to_video",
        "notes": [
            "Usa OpenRouter desde el inicio con el modelo minimax/hailuo-2.3.",
            "La imagen de referencia por defecto es la copia versionada en GitHub: Podcast/trio_de_amigos.jpg.",
            "Por defecto este script solo crea el plan; usa --submit para gastar créditos de OpenRouter.",
            "Después puedes remuxear audio con ffmpeg usando speech_audio si el clip generado no trae voz utilizable.",
        ],
        "jobs": jobs,
    }


def default_scene_audio(scene_key: str, title: str) -> str | None:
    candidate = SCENES_DIR / scene_key / f"{title}_{scene_key}.mp3"
    if candidate.exists():
        return str(candidate.resolve())
    matches = sorted((SCENES_DIR / scene_key).glob("*.mp3"))
    if matches:
        return str(matches[0].resolve())
    return None


def openrouter_headers(api_key: str, include_json: bool = True) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/JRavenelco/Animaciones_IA",
        "X-Title": "Club Celestials OpenRouter Video Pipeline",
    }
    if include_json:
        headers["Content-Type"] = "application/json"
    return headers


def openrouter_post_video(job: dict[str, Any], api_key: str) -> dict[str, Any]:
    payload = {
        "model": job["model"],
        "prompt": job["prompt"],
        "duration": job["duration"],
        "resolution": job["resolution"],
        "aspect_ratio": job["aspect_ratio"],
        "generate_audio": job["generate_audio"],
        "frame_images": [
            {
                "type": "image_url",
                "image_url": {"url": job["reference_image_url"]},
                "frame_type": "first_frame",
            }
        ],
    }
    response = requests.post(
        f"{OPENROUTER_API_BASE}/videos",
        headers=openrouter_headers(api_key),
        json=payload,
        timeout=120,
    )
    if not response.ok:
        raise RuntimeError(f"OpenRouter rechazó la tarea {job['scene']}: {response.status_code} {response.text}")
    return response.json()


def openrouter_poll(status: dict[str, Any], api_key: str) -> dict[str, Any]:
    polling_url = status.get("polling_url")
    if not polling_url:
        raise RuntimeError(f"OpenRouter no devolvió polling_url: {status}")
    poll_url = urljoin("https://openrouter.ai", polling_url)
    response = requests.get(poll_url, headers=openrouter_headers(api_key, include_json=False), timeout=60)
    if not response.ok:
        raise RuntimeError(f"No pude consultar tarea OpenRouter: {response.status_code} {response.text}")
    return response.json()


def download_video(job: dict[str, Any], status: dict[str, Any], api_key: str) -> None:
    job_id = status.get("id") or job.get("openrouter_job_id")
    if not job_id:
        raise RuntimeError(f"No hay id para descargar el video: {status}")
    download_url = (status.get("unsigned_urls") or [None])[0]
    if not download_url:
        download_url = f"{OPENROUTER_API_BASE}/videos/{job_id}/content?index=0"
    headers = openrouter_headers(api_key, include_json=False) if download_url.startswith(OPENROUTER_API_BASE) else {}

    output_path = Path(job["expected_output_video"])
    raw_output_path = output_path.with_name(f"{output_path.stem}_raw{output_path.suffix}")
    raw_output_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(download_url, headers=headers, stream=True, timeout=300) as response:
        if not response.ok:
            raise RuntimeError(f"No pude descargar video OpenRouter: {response.status_code} {response.text}")
        with raw_output_path.open("wb") as output_file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    output_file.write(chunk)
    job["downloaded_video_raw"] = str(raw_output_path)

    audio_path = Path(job["speech_audio"]) if job.get("speech_audio") else None
    if audio_path and audio_path.exists():
        remux_audio(raw_output_path, audio_path, output_path)
    else:
        shutil.copy2(raw_output_path, output_path)
    job["downloaded_video"] = str(output_path)


def remux_audio(video_path: Path, audio_path: Path, output_path: Path) -> None:
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-i",
        str(audio_path),
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(output_path),
    ]
    process = subprocess.run(command, cwd=str(output_path.parent))
    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg falló remuxeando audio para {output_path}")


def wait_for_openrouter_video(job: dict[str, Any], api_key: str, poll_seconds: int, timeout_minutes: int) -> dict[str, Any]:
    status = job["openrouter_response"]
    deadline = time.monotonic() + timeout_minutes * 60
    terminal_errors = {"failed", "cancelled", "expired"}

    while time.monotonic() < deadline:
        current_status = status.get("status")
        print(f"{job['scene']}: {current_status}")
        if current_status == "completed":
            download_video(job, status, api_key)
            job["openrouter_final_status"] = status
            return job
        if current_status in terminal_errors:
            raise RuntimeError(f"OpenRouter falló en {job['scene']}: {status}")
        time.sleep(poll_seconds)
        status = openrouter_poll(status, api_key)

    raise TimeoutError(f"Se agotó el tiempo esperando la tarea OpenRouter {job.get('openrouter_job_id')}")


def main() -> int:
    args = parse_args()
    manifest = load_json(Path(args.manifest))
    plan = build_plan(manifest, args)

    if args.submit or args.wait:
        api_key = resolve_openrouter_api_key()
        for job in plan["jobs"]:
            print(f"Enviando a OpenRouter: {job['scene']}")
            response = openrouter_post_video(job, api_key)
            job["openrouter_response"] = response
            job["openrouter_job_id"] = response.get("id")
            job["polling_url"] = response.get("polling_url")
            print(f"OpenRouter job {job['scene']}: {job.get('openrouter_job_id')}")
            if args.wait:
                wait_for_openrouter_video(job, api_key, args.poll_seconds, args.timeout_minutes)

    output_path = Path(args.output).expanduser().resolve()
    save_json(plan, output_path)
    print(f"Plan OpenRouter guardado en: {output_path}")
    if not args.submit:
        print("No se llamó a la API. Usa --submit para crear tareas pagadas; agrega --wait para descargar resultados.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
