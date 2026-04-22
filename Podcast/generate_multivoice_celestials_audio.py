import argparse
import json
import os
import sys
import wave
from pathlib import Path
from typing import Any

import requests

from podcast_env import load_local_env

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "_generated_assets"
ELEVENLABS_VOICES_URL = "https://api.elevenlabs.io/v1/voices"
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
MCP_CONFIG_PATH = Path.home() / ".codeium" / "windsurf" / "mcp_config.json"
PCM_SAMPLE_RATE = 44100
PCM_SAMPLE_WIDTH = 2
PCM_CHANNELS = 1

load_local_env(BASE_DIR)

SUPPORTED_SPEAKERS = {
    "fer": "fer",
    "rufis": "rufis",
    "serrafin": "serratin",
    "serrafin": "serratin",
    "serratin": "serratin",
    "serratín": "serratin",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dialogue-file")
    parser.add_argument("--list-voices", action="store_true")
    parser.add_argument("--title", default="club_celestials_multivoz")
    parser.add_argument("--fer-voice-id", default=os.getenv("FER_VOICE_ID"))
    parser.add_argument("--rufis-voice-id", default=os.getenv("RUFIS_VOICE_ID"))
    parser.add_argument("--serratin-voice-id", default=os.getenv("SERRATIN_VOICE_ID"))
    parser.add_argument("--model-id", default=os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"))
    parser.add_argument("--pause-ms", type=int, default=350)
    args = parser.parse_args()
    if not args.list_voices and not args.dialogue_file:
        parser.error("Debes usar --list-voices o --dialogue-file")
    return args


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Falta la variable de entorno requerida: {name}")
    return value


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


def ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def slugify(value: str) -> str:
    return "_".join(part for part in "".join(ch if ch.isalnum() else " " for ch in value).split()) or "output"


def get_json(response: requests.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"La API no devolvió JSON válido: {response.text}") from exc
    if not response.ok:
        raise RuntimeError(f"Error HTTP {response.status_code}: {payload}")
    return payload


def list_voices(api_key: str) -> list[dict[str, Any]]:
    response = requests.get(
        ELEVENLABS_VOICES_URL,
        headers={"xi-api-key": api_key, "Accept": "application/json"},
        timeout=60,
    )
    payload = get_json(response)
    voices = payload.get("voices")
    if isinstance(voices, list):
        return voices
    data = payload.get("data")
    if isinstance(data, dict) and isinstance(data.get("voices"), list):
        return data["voices"]
    return []


def print_voices(voices: list[dict[str, Any]]) -> None:
    if not voices:
        print("No encontré voces disponibles en ElevenLabs.")
        return
    for voice in voices:
        name = voice.get("name", "sin_nombre")
        voice_id = voice.get("voice_id") or voice.get("voiceId") or "sin_id"
        category = voice.get("category", "sin_categoria")
        labels = voice.get("labels") or {}
        age = labels.get("age") if isinstance(labels, dict) else None
        gender = labels.get("gender") if isinstance(labels, dict) else None
        extras = []
        if gender:
            extras.append(f"gender={gender}")
        if age:
            extras.append(f"age={age}")
        extra_text = f" ({', '.join(extras)})" if extras else ""
        print(f"{name} | {voice_id} | {category}{extra_text}")


def load_dialogue(dialogue_file: Path) -> list[dict[str, str]]:
    file_path = dialogue_file.expanduser().resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"No encontré el archivo de diálogo: {file_path}")
    dialogue = []
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if ":" not in line:
            raise RuntimeError(f"Formato inválido en línea: {raw_line}")
        speaker_raw, text_raw = line.split(":", 1)
        speaker_key = SUPPORTED_SPEAKERS.get(speaker_raw.strip().lower())
        if not speaker_key:
            raise RuntimeError(f"Personaje no soportado: {speaker_raw}")
        text = text_raw.strip()
        if not text:
            raise RuntimeError(f"Línea sin texto para {speaker_raw}")
        dialogue.append({"speaker": speaker_key, "text": text})
    if not dialogue:
        raise RuntimeError("El archivo de diálogo está vacío")
    return dialogue


def speaker_voice_map(args: argparse.Namespace) -> dict[str, str]:
    mapping = {
        "fer": args.fer_voice_id,
        "rufis": args.rufis_voice_id,
        "serratin": args.serratin_voice_id,
    }
    missing = [speaker for speaker, voice_id in mapping.items() if not voice_id]
    if missing:
        raise RuntimeError(
            "Faltan voice_id para: " + ", ".join(missing) + ". Usa --list-voices para ver las voces disponibles."
        )
    return mapping


def silence_pcm(duration_ms: int) -> bytes:
    frame_count = int(PCM_SAMPLE_RATE * duration_ms / 1000)
    return b"\x00\x00" * frame_count


def synthesize_pcm(text: str, voice_id: str, model_id: str, api_key: str) -> bytes:
    response = requests.post(
        ELEVENLABS_TTS_URL.format(voice_id=voice_id),
        params={"output_format": "pcm_44100"},
        headers={
            "xi-api-key": api_key,
            "Accept": "application/octet-stream",
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "model_id": model_id,
        },
        timeout=180,
    )
    if not response.ok:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise RuntimeError(f"Error generando audio en ElevenLabs: {detail}")
    return response.content


def write_wav(output_path: Path, pcm_data: bytes) -> Path:
    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(PCM_CHANNELS)
        wav_file.setsampwidth(PCM_SAMPLE_WIDTH)
        wav_file.setframerate(PCM_SAMPLE_RATE)
        wav_file.writeframes(pcm_data)
    return output_path


def save_json(data: dict[str, Any], output_path: Path) -> None:
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def build_multivoice_audio(args: argparse.Namespace, api_key: str) -> int:
    ensure_output_dir()
    dialogue = load_dialogue(Path(args.dialogue_file))
    voices = speaker_voice_map(args)
    title_slug = slugify(args.title)
    manifest_path = OUTPUT_DIR / f"{title_slug}_multivoz_manifest.json"
    audio_path = OUTPUT_DIR / f"{title_slug}_multivoz.wav"
    combined_pcm = bytearray()
    segments = []

    for index, item in enumerate(dialogue, start=1):
        speaker = item["speaker"]
        text = item["text"]
        voice_id = voices[speaker]
        print(f"Generando segmento {index}: {speaker}")
        pcm = synthesize_pcm(text, voice_id, args.model_id, api_key)
        segment_path = OUTPUT_DIR / f"{title_slug}_{index:02d}_{speaker}.wav"
        write_wav(segment_path, pcm)
        if combined_pcm:
            combined_pcm.extend(silence_pcm(args.pause_ms))
        combined_pcm.extend(pcm)
        segments.append(
            {
                "index": index,
                "speaker": speaker,
                "text": text,
                "voice_id": voice_id,
                "file": str(segment_path),
            }
        )

    write_wav(audio_path, bytes(combined_pcm))
    manifest = {
        "title": args.title,
        "dialogue_file": str(Path(args.dialogue_file).expanduser().resolve()),
        "audio_file": str(audio_path),
        "pause_ms": args.pause_ms,
        "segments": segments,
    }
    save_json(manifest, manifest_path)
    print(f"Audio multivoz listo: {audio_path}")
    print(f"Manifest: {manifest_path}")
    return 0


def main() -> int:
    args = parse_args()
    api_key = resolve_elevenlabs_api_key()
    if args.list_voices:
        voices = list_voices(api_key)
        print_voices(voices)
        return 0
    return build_multivoice_audio(args, api_key)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
