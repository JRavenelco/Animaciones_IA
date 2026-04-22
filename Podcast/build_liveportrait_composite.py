import argparse
import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image
from moviepy import CompositeVideoClip, ImageClip, VideoFileClip

BASE_DIR = Path(__file__).resolve().parent
SCENES_DIR = BASE_DIR / "_generated_assets" / "celestials_scenes"
DEFAULT_JOB = SCENES_DIR / "liveportrait_job.json"
DEFAULT_OUTPUT = SCENES_DIR / "club_celestials_liveportrait_final.mp4"
DEFAULT_BOXES = {
    "fer": [0.31, 0.11, 0.66, 0.90],
    "rufis": [0.05, 0.16, 0.35, 0.90],
    "serratin": [0.65, 0.16, 0.95, 0.90],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", default=str(DEFAULT_JOB))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--mode", choices=["sequential", "simultaneous"], default="sequential")
    parser.add_argument("--gap", type=float, default=0.0)
    return parser.parse_args()


def load_job(job_path: Path) -> dict[str, Any]:
    resolved = job_path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"No encontré el archivo de job: {resolved}")
    return json.loads(resolved.read_text(encoding="utf-8"))


def background_size(image_path: Path) -> tuple[int, int]:
    with Image.open(image_path) as image:
        return image.size


def resolve_box(job: dict[str, Any]) -> list[float]:
    compose_box = job.get("compose_box_rel")
    if isinstance(compose_box, list) and len(compose_box) == 4:
        return [float(value) for value in compose_box]
    scene = job.get("scene")
    if scene in DEFAULT_BOXES:
        return DEFAULT_BOXES[scene]
    raise RuntimeError(f"No encontré compose_box_rel para escena: {job}")


def clip_geometry(box: list[float], frame_size: tuple[int, int]) -> tuple[int, int, int, int]:
    width, height = frame_size
    left = int(width * box[0])
    top = int(height * box[1])
    right = int(width * box[2])
    bottom = int(height * box[3])
    return left, top, max(1, right - left), max(1, bottom - top)


def build_scene_clip(job: dict[str, Any], frame_size: tuple[int, int], start_time: float) -> tuple[VideoFileClip, float]:
    output_video = job.get("expected_output_video")
    if not output_video:
        raise RuntimeError(f"Falta expected_output_video en job: {job}")
    video_path = Path(output_video)
    if not video_path.exists():
        raise FileNotFoundError(f"No encontré el video de LivePortrait: {video_path}")

    box = resolve_box(job)
    left, top, target_width, target_height = clip_geometry(box, frame_size)
    clip = VideoFileClip(str(video_path)).resized((target_width, target_height)).with_position((left, top))
    clip = clip.with_start(start_time)
    return clip, clip.duration


def build_timeline(jobs: list[dict[str, Any]], frame_size: tuple[int, int], mode: str, gap: float) -> tuple[list[VideoFileClip], float]:
    clips = []
    current_start = 0.0
    max_end = 0.0
    for job in jobs:
        start_time = 0.0 if mode == "simultaneous" else current_start
        clip, duration = build_scene_clip(job, frame_size, start_time)
        clips.append(clip)
        end_time = start_time + duration
        max_end = max(max_end, end_time)
        if mode == "sequential":
            current_start = end_time + gap
    return clips, max_end


def main() -> int:
    args = parse_args()
    job_data = load_job(Path(args.job))
    background_image = job_data.get("background_image")
    jobs = job_data.get("jobs") or []
    if not background_image:
        raise RuntimeError("El job no contiene background_image")
    if not jobs:
        raise RuntimeError("El job no contiene escenas")

    background_path = Path(background_image)
    if not background_path.exists():
        raise FileNotFoundError(f"No encontré la imagen de fondo: {background_path}")

    frame_size = background_size(background_path)
    clips, total_duration = build_timeline(jobs, frame_size, args.mode, args.gap)
    background_clip = ImageClip(str(background_path)).with_duration(total_duration)
    final_clip = CompositeVideoClip([background_clip, *clips], size=frame_size)

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_clip.write_videofile(str(output_path), fps=args.fps, codec="libx264", audio_codec="aac")

    final_clip.close()
    background_clip.close()
    for clip in clips:
        if clip.audio is not None:
            clip.audio.close()
        clip.close()

    print(f"Video compuesto listo: {output_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
