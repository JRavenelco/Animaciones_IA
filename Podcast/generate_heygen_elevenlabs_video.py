import argparse
import json
import mimetypes
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests
from PIL import Image

from podcast_env import load_local_env

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_IMAGE = BASE_DIR / "a6d11588-9d4e-44f1-bf66-81f5eca189ec.jfif"
OUTPUT_DIR = BASE_DIR / "_generated_assets"
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
HEYGEN_UPLOAD_URL = "https://upload.heygen.com/v1/asset"
HEYGEN_VIDEO_URL = "https://api.heygen.com/v2/video/generate"
HEYGEN_VIDEO_STATUS_URL = "https://api.heygen.com/v1/video_status.get"
MCP_CONFIG_PATH = Path.home() / ".codeium" / "windsurf" / "mcp_config.json"

load_local_env(BASE_DIR)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    text_group = parser.add_mutually_exclusive_group(required=True)
    text_group.add_argument("--text")
    text_group.add_argument("--text-file")
    parser.add_argument("--voice-id", required=True)
    parser.add_argument("--image", default=str(DEFAULT_IMAGE))
    parser.add_argument("--title", default="Podcast Video")
    parser.add_argument("--talking-photo-id", default=os.getenv("HEYGEN_TALKING_PHOTO_ID"))
    parser.add_argument("--elevenlabs-model", default=os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2"))
    parser.add_argument("--poll-interval", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--skip-poll", action="store_true")
    parser.add_argument("--download", action="store_true")
    return parser.parse_args()


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


def resolve_heygen_api_key() -> str:
    value = os.getenv("HEYGEN_API_KEY")
    if value:
        return value
    value = load_key_from_mcp_config("HeyGen", "HEYGEN_API_KEY")
    if value:
        return value
    raise RuntimeError("No encontré HEYGEN_API_KEY ni en variables de entorno ni en .codeium/windsurf/mcp_config.json")


def slugify(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip()).strip("_")
    return clean or "output"


def ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def load_text(args: argparse.Namespace) -> str:
    if args.text:
        return args.text.strip()

    text_file = Path(args.text_file).expanduser().resolve()
    if not text_file.exists():
        raise FileNotFoundError(f"No encontré el archivo de texto: {text_file}")

    content = text_file.read_text(encoding="utf-8").strip()
    if not content:
        raise RuntimeError(f"El archivo de texto está vacío: {text_file}")
    return content


def prepare_image(image_path: Path) -> Path:
    image_path = image_path.expanduser().resolve()
    if not image_path.exists():
        raise FileNotFoundError(f"No encontré la imagen: {image_path}")

    suffix = image_path.suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png"}:
        return image_path

    output_dir = ensure_output_dir()
    converted_path = output_dir / f"{image_path.stem}.jpg"
    with Image.open(image_path) as image:
        rgb = image.convert("RGB")
        rgb.save(converted_path, format="JPEG", quality=95)
    return converted_path


def detect_mime_type(file_path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if mime_type:
        return mime_type
    if file_path.suffix.lower() == ".mp3":
        return "audio/mpeg"
    if file_path.suffix.lower() in {".jpg", ".jpeg", ".jfif"}:
        return "image/jpeg"
    if file_path.suffix.lower() == ".png":
        return "image/png"
    return "application/octet-stream"


def check_response(response: requests.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError:
        payload = None

    if not response.ok:
        detail = payload if payload is not None else response.text
        raise RuntimeError(f"Error HTTP {response.status_code}: {detail}")

    if isinstance(payload, dict):
        error = payload.get("error")
        code = payload.get("code")
        if error:
            raise RuntimeError(f"Error de API: {error}")
        if code not in (None, 100, "100") and payload.get("data") is None:
            raise RuntimeError(f"Respuesta inesperada de API: {payload}")
        return payload

    raise RuntimeError("La API no devolvió JSON válido")


def generate_elevenlabs_audio(text: str, voice_id: str, model_id: str, api_key: str, output_path: Path) -> Path:
    url = ELEVENLABS_TTS_URL.format(voice_id=voice_id)
    response = requests.post(
        url,
        params={"output_format": "mp3_44100_128"},
        headers={
            "xi-api-key": api_key,
            "Accept": "audio/mpeg",
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

    output_path.write_bytes(response.content)
    return output_path


def upload_heygen_asset(file_path: Path, api_key: str) -> dict[str, Any]:
    response = requests.post(
        HEYGEN_UPLOAD_URL,
        headers={
            "X-Api-Key": api_key,
            "Content-Type": detect_mime_type(file_path),
        },
        data=file_path.read_bytes(),
        timeout=180,
    )
    payload = check_response(response)
    data = payload.get("data") or {}
    if not data.get("id"):
        raise RuntimeError(f"No recibí asset id de HeyGen: {payload}")
    return data


def create_heygen_video(title: str, talking_photo_id: str, audio_asset_id: str, api_key: str) -> dict[str, Any]:
    body = {
        "title": title,
        "caption": False,
        "video_inputs": [
            {
                "character": {
                    "type": "talking_photo",
                    "talking_photo_id": talking_photo_id,
                },
                "voice": {
                    "type": "audio",
                    "audio_asset_id": audio_asset_id,
                },
            }
        ],
    }
    response = requests.post(
        HEYGEN_VIDEO_URL,
        headers={
            "X-Api-Key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json=body,
        timeout=180,
    )
    payload = check_response(response)
    data = payload.get("data") or {}
    if not data.get("video_id"):
        raise RuntimeError(f"No recibí video_id de HeyGen: {payload}")
    return data


def get_heygen_video_status(video_id: str, api_key: str) -> dict[str, Any]:
    response = requests.get(
        HEYGEN_VIDEO_STATUS_URL,
        headers={
            "X-Api-Key": api_key,
            "Accept": "application/json",
        },
        params={"video_id": video_id},
        timeout=60,
    )
    payload = check_response(response)
    data = payload.get("data") or {}
    return data


def extract_video_url(data: Any) -> str | None:
    if isinstance(data, dict):
        for key in ("video_url", "url", "download_url"):
            value = data.get(key)
            if isinstance(value, str) and value.startswith("http"):
                return value
        for value in data.values():
            found = extract_video_url(value)
            if found:
                return found
    if isinstance(data, list):
        for item in data:
            found = extract_video_url(item)
            if found:
                return found
    return None


def extract_status(data: Any) -> str:
    if isinstance(data, dict):
        for key in ("status", "video_status"):
            value = data.get(key)
            if isinstance(value, str):
                return value.lower()
        for value in data.values():
            found = extract_status(value)
            if found:
                return found
    if isinstance(data, list):
        for item in data:
            found = extract_status(item)
            if found:
                return found
    return "unknown"


def download_file(url: str, output_path: Path) -> Path:
    with requests.get(url, stream=True, timeout=300) as response:
        response.raise_for_status()
        with output_path.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
    return output_path


def save_json(data: dict[str, Any], output_path: Path) -> None:
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    args = parse_args()
    ensure_output_dir()

    elevenlabs_api_key = resolve_elevenlabs_api_key()
    heygen_api_key = resolve_heygen_api_key()
    text = load_text(args)

    image_path = prepare_image(Path(args.image))
    title_slug = slugify(args.title)
    audio_path = OUTPUT_DIR / f"{title_slug}.mp3"
    manifest_path = OUTPUT_DIR / f"{title_slug}_manifest.json"
    status_path = OUTPUT_DIR / f"{title_slug}_status.json"
    video_path = OUTPUT_DIR / f"{title_slug}.mp4"

    print(f"Imagen lista: {image_path}")
    generated_audio = generate_elevenlabs_audio(
        text=text,
        voice_id=args.voice_id,
        model_id=args.elevenlabs_model,
        api_key=elevenlabs_api_key,
        output_path=audio_path,
    )
    print(f"Audio generado: {generated_audio}")

    image_asset = upload_heygen_asset(image_path, heygen_api_key)
    audio_asset = upload_heygen_asset(generated_audio, heygen_api_key)

    manifest = {
        "image_path": str(image_path),
        "audio_path": str(generated_audio),
        "image_asset": image_asset,
        "audio_asset": audio_asset,
        "talking_photo_id": args.talking_photo_id,
        "title": args.title,
    }
    save_json(manifest, manifest_path)
    print(f"Assets subidos. Manifest: {manifest_path}")
    print(f"image_asset_id: {image_asset.get('id')}")
    print(f"audio_asset_id: {audio_asset.get('id')}")

    if not args.talking_photo_id:
        print("No se proporcionó talking_photo_id. El audio y la imagen ya quedaron listos en HeyGen.")
        print("Crea o identifica tu Photo Avatar/Talking Photo en HeyGen y vuelve a correr el script con --talking-photo-id.")
        return 0

    video_data = create_heygen_video(
        title=args.title,
        talking_photo_id=args.talking_photo_id,
        audio_asset_id=audio_asset["id"],
        api_key=heygen_api_key,
    )
    video_id = video_data["video_id"]
    manifest["video"] = video_data
    save_json(manifest, manifest_path)
    print(f"Video solicitado en HeyGen. video_id: {video_id}")

    if args.skip_poll:
        return 0

    started = time.time()
    last_status = None
    while True:
        status_data = get_heygen_video_status(video_id, heygen_api_key)
        save_json(status_data, status_path)
        status = extract_status(status_data)
        if status != last_status:
            print(f"Estado: {status}")
            last_status = status

        if status in {"completed", "complete", "finished", "success", "succeeded"}:
            video_url = extract_video_url(status_data)
            if video_url:
                print(f"Video listo: {video_url}")
                if args.download:
                    download_file(video_url, video_path)
                    print(f"Video descargado: {video_path}")
            else:
                print("El video terminó, pero no encontré la URL de salida en la respuesta.")
            return 0

        if status in {"failed", "error"}:
            raise RuntimeError(f"La generación del video falló: {status_data}")

        elapsed = time.time() - started
        if elapsed > args.timeout:
            raise TimeoutError(f"Tiempo de espera agotado tras {args.timeout} segundos")

        time.sleep(args.poll_interval)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
