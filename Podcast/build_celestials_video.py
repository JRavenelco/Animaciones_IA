import argparse
import json
import sys
from pathlib import Path

from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MANIFEST = BASE_DIR / "_generated_assets" / "celestials_scenes" / "club_celestials_escenas_manifest.json"
DEFAULT_OUTPUT = BASE_DIR / "_generated_assets" / "celestials_scenes" / "club_celestials_final.mp4"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--fps", type=int, default=24)
    return parser.parse_args()


def load_manifest(manifest_path: Path) -> dict:
    resolved = manifest_path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"No encontré el manifest: {resolved}")
    return json.loads(resolved.read_text(encoding="utf-8"))


def build_clip(image_path: Path, audio_path: Path):
    audio_clip = AudioFileClip(str(audio_path))
    image_clip = ImageClip(str(image_path)).set_duration(audio_clip.duration).set_audio(audio_clip)
    return image_clip


def main() -> int:
    args = parse_args()
    manifest = load_manifest(Path(args.manifest))
    scenes = manifest.get("scenes") or []
    if not scenes:
        raise RuntimeError("El manifest no contiene escenas")

    clips = []
    for scene in scenes:
        image_file = scene.get("image_file")
        audio_file = scene.get("audio_file")
        if not image_file or not audio_file:
            raise RuntimeError(f"Faltan archivos de imagen o audio en escena: {scene}")
        image_path = Path(image_file)
        audio_path = Path(audio_file)
        if not image_path.exists():
            raise FileNotFoundError(f"No encontré la imagen de escena: {image_path}")
        if not audio_path.exists():
            raise FileNotFoundError(f"No encontré el audio de escena: {audio_path}")
        clips.append(build_clip(image_path, audio_path))

    final_clip = concatenate_videoclips(clips, method="compose")
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_clip.write_videofile(str(output_path), fps=args.fps, codec="libx264", audio_codec="aac")
    final_clip.close()
    for clip in clips:
        if clip.audio is not None:
            clip.audio.close()
        clip.close()
    print(f"Video final listo: {output_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
