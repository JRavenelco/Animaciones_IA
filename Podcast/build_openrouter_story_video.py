from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OPENROUTER_DIR = BASE_DIR / "_generated_assets" / "openrouter_scenes"
CELESTIALS_DIR = BASE_DIR / "_generated_assets" / "celestials_scenes"
DEFAULT_OUTPUT = OPENROUTER_DIR / "club_celestials_openrouter_story_final.mp4"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--include-serratin", action="store_true")
    parser.add_argument("--pause-duration", type=float, default=0.65)
    return parser.parse_args()


def run_command(command: list[str], cwd: Path) -> None:
    process = subprocess.run(command, cwd=str(cwd))
    if process.returncode != 0:
        raise RuntimeError(f"El comando falló con código {process.returncode}: {' '.join(command)}")


def remux_audio(video_path: Path, audio_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-stream_loop",
        "-1",
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
    run_command(command, output_path.parent)
    return output_path


def normalize_clip(input_path: Path, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-vf",
        "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1",
        "-r",
        "24",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-ar",
        "44100",
        "-ac",
        "2",
        str(output_path),
    ]
    run_command(command, output_path.parent)
    return output_path


def build_pause(output_path: Path, duration: float) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "color=c=black:s=1920x1080:r=24",
        "-f",
        "lavfi",
        "-i",
        "anullsrc=channel_layout=stereo:sample_rate=44100",
        "-t",
        str(duration),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        str(output_path),
    ]
    run_command(command, output_path.parent)
    return output_path


def concat_clips(clips: list[Path], output_path: Path) -> Path:
    list_path = output_path.parent / "openrouter_story_concat.txt"
    lines = [f"file '{clip.as_posix()}'" for clip in clips]
    list_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    command = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_path),
        "-c",
        "copy",
        str(output_path),
    ]
    run_command(command, output_path.parent)
    return output_path


def main() -> int:
    args = parse_args()
    output_path = Path(args.output).expanduser().resolve()
    work_dir = OPENROUTER_DIR / "_story_work"

    sources = [
        (
            OPENROUTER_DIR / "fer" / "club_celestials_escenas_fer_openrouter_raw.mp4",
            OPENROUTER_DIR / "fer" / "club_celestials_escenas_fer_short.mp3",
            work_dir / "01_fer.mp4",
        ),
        (
            OPENROUTER_DIR / "rufis" / "club_celestials_escenas_rufis_openrouter_raw.mp4",
            OPENROUTER_DIR / "rufis" / "club_celestials_escenas_rufis_short.mp3",
            work_dir / "02_rufis.mp4",
        ),
        (
            OPENROUTER_DIR / "serratin" / "club_celestials_escenas_serratin_openrouter_raw.mp4",
            OPENROUTER_DIR / "serratin" / "club_celestials_escenas_serratin_short.mp3",
            work_dir / "03_serratin.mp4",
        ),
    ]

    normalized = []
    for index, (video_path, audio_path, output_clip) in enumerate(sources):
        if not video_path.exists():
            raise FileNotFoundError(f"No encontré video: {video_path}")
        if not audio_path.exists():
            raise FileNotFoundError(f"No encontré audio corto: {audio_path}")
        remuxed = output_clip.with_name(output_clip.stem + "_remux.mp4")
        remux_audio(video_path, audio_path, remuxed)
        normalized.append(normalize_clip(remuxed, output_clip))
        if args.pause_duration > 0 and index < len(sources) - 1:
            normalized.append(build_pause(work_dir / f"pause_{index + 1:02d}.mp4", args.pause_duration))

    concat_clips(normalized, output_path)
    print(f"Video story listo: {output_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
