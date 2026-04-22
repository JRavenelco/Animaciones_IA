import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import requests
from PIL import Image, ImageFilter

from podcast_env import load_local_env

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_IMAGE = BASE_DIR / "trio_de_amigos.jpg"
OUTPUT_DIR = BASE_DIR / "_generated_assets" / "celestials_scenes"
MCP_CONFIG_PATH = Path.home() / ".codeium" / "windsurf" / "mcp_config.json"
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
CANVAS_SIZE = (1280, 720)

load_local_env(BASE_DIR)

SCENE_CONFIG = {
    "fer": {
        "label": "Fer",
        "text_file": BASE_DIR / "club_celestials_fer.txt",
        "crop_box_rel": (0.30, 0.08, 0.69, 0.93),
        "compose_box_rel": (0.31, 0.11, 0.66, 0.90),
        "voice_env": "FER_VOICE_ID",
        "voice_settings": {
            "stability": 0.38,
            "similarity_boost": 0.82,
            "style": 0.18,
            "use_speaker_boost": True,
        },
    },
    "rufis": {
        "label": "Rufis",
        "text_file": BASE_DIR / "club_celestials_rufis.txt",
        "crop_box_rel": (0.06, 0.12, 0.42, 0.93),
        "compose_box_rel": (0.05, 0.16, 0.35, 0.90),
        "voice_env": "RUFIS_VOICE_ID",
        "voice_settings": {
            "stability": 0.48,
            "similarity_boost": 0.76,
            "style": 0.12,
            "use_speaker_boost": True,
        },
    },
    "serratin": {
        "label": "Serratín",
        "text_file": BASE_DIR / "club_celestials_serratin.txt",
        "crop_box_rel": (0.55, 0.05, 0.98, 0.95),
        "compose_box_rel": (0.65, 0.16, 0.95, 0.90),
        "voice_env": "SERRATIN_VOICE_ID",
        "voice_settings": {
            "stability": 0.46,
            "similarity_boost": 0.76,
            "style": 0.1,
            "use_speaker_boost": True,
        },
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default=str(DEFAULT_IMAGE))
    parser.add_argument("--title", default="club_celestials_escenas")
    parser.add_argument("--model-id", default=os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"))
    parser.add_argument("--fer-voice-id", default=os.getenv("FER_VOICE_ID"))
    parser.add_argument("--rufis-voice-id", default=os.getenv("RUFIS_VOICE_ID"))
    parser.add_argument("--serratin-voice-id", default=os.getenv("SERRATIN_VOICE_ID"))
    parser.add_argument("--images-only", action="store_true")
    return parser.parse_args()


def ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def slugify(value: str) -> str:
    return "_".join(part for part in "".join(ch if ch.isalnum() else " " for ch in value).split()) or "output"


def load_key_from_mcp_config(server_name: str, env_name: str) -> str | None:
    if not MCP_CONFIG_PATH.exists():
        return None
    try:
        payload = json.loads(MCP_CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None
    server = ((payload.get("mcpServers") or {}).get(server_name) or {})
    env = server.get("env") or {}
    value = env.get(env_name)
    return value or None


def resolve_elevenlabs_api_key() -> str:
    value = os.getenv("ELEVENLABS_API_KEY")
    if value:
        return value
    value = load_key_from_mcp_config("ElevenLabs", "ELEVENLABS_API_KEY")
    if value:
        return value
    raise RuntimeError("No encontré ELEVENLABS_API_KEY ni en variables de entorno ni en .codeium/windsurf/mcp_config.json")


def read_text_file(file_path: Path) -> str:
    resolved = file_path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"No encontré el archivo de texto: {resolved}")
    content = resolved.read_text(encoding="utf-8").strip()
    if not content:
        raise RuntimeError(f"El archivo está vacío: {resolved}")
    return content


def crop_relative(image: Image.Image, crop_box_rel: tuple[float, float, float, float]) -> Image.Image:
    width, height = image.size
    left = int(width * crop_box_rel[0])
    top = int(height * crop_box_rel[1])
    right = int(width * crop_box_rel[2])
    bottom = int(height * crop_box_rel[3])
    return image.crop((left, top, right, bottom))


def cover_resize(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    width, height = image.size
    target_width, target_height = size
    scale = max(target_width / width, target_height / height)
    resized = image.resize((int(width * scale), int(height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - target_width) // 2
    top = (resized.height - target_height) // 2
    return resized.crop((left, top, left + target_width, top + target_height))


def fit_inside(image: Image.Image, size: tuple[int, int]) -> Image.Image:
    width, height = image.size
    target_width, target_height = size
    scale = min(target_width / width, target_height / height)
    return image.resize((int(width * scale), int(height * scale)), Image.Resampling.LANCZOS)


def build_scene_image(source_image: Image.Image, crop_box_rel: tuple[float, float, float, float]) -> Image.Image:
    crop = crop_relative(source_image, crop_box_rel).convert("RGB")
    background = cover_resize(crop, CANVAS_SIZE).filter(ImageFilter.GaussianBlur(radius=24))
    background = Image.blend(background, Image.new("RGB", CANVAS_SIZE, (245, 245, 245)), 0.18)
    foreground = fit_inside(crop, (int(CANVAS_SIZE[0] * 0.86), int(CANVAS_SIZE[1] * 0.92)))
    canvas = background.copy()
    left = (CANVAS_SIZE[0] - foreground.width) // 2
    top = (CANVAS_SIZE[1] - foreground.height) // 2
    canvas.paste(foreground, (left, top))
    return canvas


def generate_audio(text: str, voice_id: str, model_id: str, api_key: str, output_path: Path, voice_settings: dict[str, Any]) -> Path:
    response = requests.post(
        ELEVENLABS_TTS_URL.format(voice_id=voice_id),
        params={"output_format": "mp3_44100_128"},
        headers={
            "xi-api-key": api_key,
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "model_id": model_id,
            "voice_settings": voice_settings,
        },
        timeout=180,
    )
    if not response.ok:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise RuntimeError(f"Error generando audio en ElevenLabs: {detail}")
    output_path.write_bytes(response.content)
    return output_path


def save_json(data: dict[str, Any], output_path: Path) -> None:
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    args = parse_args()
    ensure_output_dir()
    image_path = Path(args.image).expanduser().resolve()
    if not image_path.exists():
        raise FileNotFoundError(f"No encontré la imagen: {image_path}")

    api_key = None if args.images_only else resolve_elevenlabs_api_key()
    voice_ids = {
        "fer": args.fer_voice_id,
        "rufis": args.rufis_voice_id,
        "serratin": args.serratin_voice_id,
    }

    manifest = {
        "title": args.title,
        "image": str(image_path),
        "images_only": args.images_only,
        "background_strategy": "original_group_image",
        "scenes": [],
    }
    title_slug = slugify(args.title)

    with Image.open(image_path) as source_image:
        for scene_key, config in SCENE_CONFIG.items():
            scene_dir = OUTPUT_DIR / scene_key
            scene_dir.mkdir(parents=True, exist_ok=True)
            text = read_text_file(config["text_file"])
            scene_image = build_scene_image(source_image, config["crop_box_rel"])
            image_output = scene_dir / f"{title_slug}_{scene_key}.jpg"
            scene_image.save(image_output, format="JPEG", quality=95)

            scene_info = {
                "scene": scene_key,
                "label": config["label"],
                "text_file": str(config["text_file"]),
                "image_file": str(image_output),
                "crop_box_rel": config["crop_box_rel"],
                "compose_box_rel": config["compose_box_rel"],
            }

            voice_id = voice_ids.get(scene_key)
            if not args.images_only and voice_id:
                audio_output = scene_dir / f"{title_slug}_{scene_key}.mp3"
                generate_audio(text, voice_id, args.model_id, api_key, audio_output, config["voice_settings"])
                scene_info["audio_file"] = str(audio_output)
                scene_info["voice_id"] = voice_id
                scene_info["voice_settings"] = config["voice_settings"]
            elif not args.images_only:
                scene_info["audio_pending"] = True

            manifest["scenes"].append(scene_info)
            print(f"Escena lista: {config['label']} -> {image_output}")

    manifest_path = OUTPUT_DIR / f"{title_slug}_manifest.json"
    save_json(manifest, manifest_path)
    print(f"Manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
