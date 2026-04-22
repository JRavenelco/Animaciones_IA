import argparse
import base64
import json
import mimetypes
import os
import sys
from pathlib import Path
from typing import Any

import requests

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_IMAGE = BASE_DIR / "trio_de_amigos.jpg"
DEFAULT_OUTPUT = BASE_DIR / "_generated_assets" / "celestials_scenes" / "gemini_suggestions.json"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-1.5-flash"
SCRIPT_FILES = {
    "fer": BASE_DIR / "club_celestials_fer.txt",
    "rufis": BASE_DIR / "club_celestials_rufis.txt",
    "serratin": BASE_DIR / "club_celestials_serratin.txt",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", default=str(DEFAULT_IMAGE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--api-key", default=os.getenv("GEMINI_API_KEY"))
    parser.add_argument("--apply-scripts", action="store_true")
    return parser.parse_args()


def require_api_key(value: str | None) -> str:
    if value:
        return value
    raise RuntimeError("Falta GEMINI_API_KEY. Pásala con --api-key o como variable de entorno.")


def read_scripts() -> dict[str, str]:
    data = {}
    for key, path in SCRIPT_FILES.items():
        data[key] = path.read_text(encoding="utf-8").strip()
    return data


def detect_mime(file_path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or "image/jpeg"


def build_prompt(existing_scripts: dict[str, str]) -> str:
    return (
        "Analiza esta imagen de tres personajes infantiles estilo caricatura y devuelve SOLO JSON válido. "
        "Necesito mejorar los guiones de presentación de Fer, Rufis y Serratín, haciendo que suenen naturales, tiernos y expresivos en español latino. "
        "Además, necesito sugerencias de recorte y composición para producir un video final donde los tres aparezcan juntos como en la imagen original. "
        "Usa siempre el nombre Serratín en los guiones reescritos. "
        "Evita por completo descriptores raciales, de tono de piel o de color de cabello, incluyendo palabras como güero, moreno, rubio, blanco, negro o similares. "
        "Evita lenguaje ofensivo, estereotipos o adjetivos basados en apariencia étnica. "
        "Devuelve un objeto JSON con esta estructura exacta: "
        "{"
        "\"improved_scripts\": {\"fer\": string, \"rufis\": string, \"serratin\": string},"
        "\"crop_suggestions\": {"
        "\"fer\": {\"crop_box_rel\": [left, top, right, bottom], \"compose_box_rel\": [left, top, right, bottom]},"
        "\"rufis\": {\"crop_box_rel\": [left, top, right, bottom], \"compose_box_rel\": [left, top, right, bottom]},"
        "\"serratin\": {\"crop_box_rel\": [left, top, right, bottom], \"compose_box_rel\": [left, top, right, bottom]}"
        "},"
        "\"notes\": string,"
        "\"recommended_pipeline\": string"
        "}. "
        "Todas las coordenadas deben ser relativas entre 0 y 1. "
        "Los recortes deben ser más cerrados al rostro y torso, pero sin perder alas o rasgos importantes. "
        "En notes menciona si algún guion original requería limpieza por lenguaje basado en apariencia. "
        f"Guiones actuales: {json.dumps(existing_scripts, ensure_ascii=False)}"
    )


def call_gemini(api_key: str, model: str, image_path: Path, prompt: str) -> dict[str, Any]:
    image_bytes = image_path.read_bytes()
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": detect_mime(image_path),
                            "data": base64.b64encode(image_bytes).decode("utf-8"),
                        }
                    },
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.6,
            "response_mime_type": "application/json",
        },
    }
    response = requests.post(
        GEMINI_API_URL.format(model=model),
        params={"key": api_key},
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=180,
    )
    if not response.ok:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise RuntimeError(f"Error llamando Gemini: {detail}")
    result = response.json()
    candidates = result.get("candidates") or []
    if not candidates:
        raise RuntimeError(f"Respuesta inesperada de Gemini: {result}")
    parts = ((candidates[0].get("content") or {}).get("parts") or [])
    text_chunks = [part.get("text", "") for part in parts if isinstance(part, dict)]
    raw_text = "".join(text_chunks).strip()
    if not raw_text:
        raise RuntimeError(f"Gemini no devolvió texto utilizable: {result}")
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Gemini no devolvió JSON válido: {raw_text}") from exc


def validate_box(box: Any) -> list[float]:
    if not isinstance(box, list) or len(box) != 4:
        raise RuntimeError(f"Caja inválida: {box}")
    values = [float(x) for x in box]
    if not all(0 <= x <= 1 for x in values):
        raise RuntimeError(f"Caja fuera de rango 0..1: {box}")
    return values


def normalize_result(data: dict[str, Any]) -> dict[str, Any]:
    improved = data.get("improved_scripts") or {}
    crops = data.get("crop_suggestions") or {}
    normalized = {
        "improved_scripts": {},
        "crop_suggestions": {},
        "notes": data.get("notes", ""),
        "recommended_pipeline": data.get("recommended_pipeline", ""),
    }
    for key in SCRIPT_FILES:
        script = improved.get(key)
        if not isinstance(script, str) or not script.strip():
            raise RuntimeError(f"Gemini no devolvió guion válido para {key}")
        crop = crops.get(key) or {}
        normalized["improved_scripts"][key] = script.strip()
        normalized["crop_suggestions"][key] = {
            "crop_box_rel": validate_box(crop.get("crop_box_rel")),
            "compose_box_rel": validate_box(crop.get("compose_box_rel")),
        }
    return normalized


def apply_scripts(data: dict[str, Any]) -> None:
    for key, path in SCRIPT_FILES.items():
        path.write_text(data["improved_scripts"][key] + "\n", encoding="utf-8")


def save_output(output_path: Path, data: dict[str, Any]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    args = parse_args()
    api_key = require_api_key(args.api_key)
    image_path = Path(args.image).expanduser().resolve()
    if not image_path.exists():
        raise FileNotFoundError(f"No encontré la imagen: {image_path}")
    existing_scripts = read_scripts()
    prompt = build_prompt(existing_scripts)
    raw_result = call_gemini(api_key, args.model, image_path, prompt)
    normalized = normalize_result(raw_result)
    output_path = Path(args.output).expanduser().resolve()
    save_output(output_path, normalized)
    if args.apply_scripts:
        apply_scripts(normalized)
        print("Guiones actualizados desde Gemini.")
    print(f"Sugerencias guardadas en: {output_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
