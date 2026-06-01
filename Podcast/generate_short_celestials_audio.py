from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import requests

from podcast_env import load_local_env

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "_generated_assets" / "openrouter_scenes"
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

load_local_env(BASE_DIR.parent)
load_local_env(BASE_DIR)

DEFAULT_VOICES = {
    "fer": "cgSgspJ2msm6clMCkdW9",
    "rufis": "IKne3meq5aSn9XLyUdCD",
    "serratin": "JBFqnCBsd6RMkjVDRZzb",
}

SHORT_LINES = {
    "fer": "¡Hola! Soy Fer, la chispa del Club Celestials. Hoy venimos a brillar contigo.",
    "rufis": "Yo soy Rufis, el angelito del equipo. Traigo risas, alas y mucha buena vibra.",
    "serratin": "Y yo soy Serratín. Juntos hacemos magia, amistad y aventuras inolvidables.",
}

VOICE_SETTINGS = {
    "fer": {"stability": 0.38, "similarity_boost": 0.82, "style": 0.18, "use_speaker_boost": True},
    "rufis": {"stability": 0.48, "similarity_boost": 0.76, "style": 0.12, "use_speaker_boost": True},
    "serratin": {"stability": 0.46, "similarity_boost": 0.76, "style": 0.10, "use_speaker_boost": True},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", choices=["fer", "rufis", "serratin"])
    parser.add_argument("--model-id", default=os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"))
    return parser.parse_args()


def valid_voice_id(value: str | None) -> bool:
    return bool(value and not value.startswith("el_id_de_") and value != "tu_voice_id")


def resolve_voice_id(scene: str) -> str:
    env_name = {
        "fer": "FER_VOICE_ID",
        "rufis": "RUFIS_VOICE_ID",
        "serratin": "SERRATIN_VOICE_ID",
    }[scene]
    env_value = os.getenv(env_name)
    return env_value if valid_voice_id(env_value) else DEFAULT_VOICES[scene]


def resolve_api_key() -> str:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("Falta ELEVENLABS_API_KEY en .env o Podcast/.env")
    return api_key


def generate_audio(scene: str, text: str, voice_id: str, model_id: str, api_key: str, output_path: Path, voice_settings: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
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
        raise RuntimeError(f"Error generando audio corto para {scene}: {response.status_code} {response.text}")
    output_path.write_bytes(response.content)


def main() -> int:
    args = parse_args()
    api_key = resolve_api_key()
    scenes = [args.scene] if args.scene else ["fer", "rufis", "serratin"]
    for scene in scenes:
        output_path = OUTPUT_DIR / scene / f"club_celestials_escenas_{scene}_short.mp3"
        generate_audio(
            scene=scene,
            text=SHORT_LINES[scene],
            voice_id=resolve_voice_id(scene),
            model_id=args.model_id,
            api_key=api_key,
            output_path=output_path,
            voice_settings=VOICE_SETTINGS[scene],
        )
        print(f"Audio corto listo: {output_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
