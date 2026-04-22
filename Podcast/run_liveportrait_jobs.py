import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
SCENES_DIR = BASE_DIR / "_generated_assets" / "celestials_scenes"
DEFAULT_JOB = SCENES_DIR / "liveportrait_job.json"
DEFAULT_LIVEPORTRAIT_ROOT = BASE_DIR.parent / "LivePortrait"
DEFAULT_PYTHON = DEFAULT_LIVEPORTRAIT_ROOT / ".venv" / "Scripts" / "python.exe"

PYTHON_ENV_VARS_TO_CLEAR = [
    "PYTHONHOME",
    "PYTHONPATH",
    "PYTHONSTARTUP",
    "__PYVENV_LAUNCHER__",
    "CUDA_PATH",
    "CUDA_HOME",
    "CUDA_PATH_V12_1",
    "CUDA_PATH_V12_4",
    "CUDA_PATH_V12_8",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", default=str(DEFAULT_JOB))
    parser.add_argument("--liveportrait-root", default=str(DEFAULT_LIVEPORTRAIT_ROOT))
    parser.add_argument("--python-exe", default=str(DEFAULT_PYTHON))
    parser.add_argument("--scene")
    parser.add_argument("--skip-audio-remux", action="store_true")
    parser.add_argument("--force-cpu", action="store_true")
    return parser.parse_args()


def load_job(path: Path) -> dict[str, Any]:
    resolved = path.expanduser().resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"No encontré el job de LivePortrait: {resolved}")
    return json.loads(resolved.read_text(encoding="utf-8"))


def build_clean_python_env(python_exe: Path) -> dict[str, str]:
    env = os.environ.copy()
    for key in PYTHON_ENV_VARS_TO_CLEAR:
        env.pop(key, None)
    site_packages_dir = python_exe.parent.parent / "Lib" / "site-packages"
    extra_paths = [
        str(python_exe.parent),
        str(site_packages_dir / "torch" / "lib"),
        str(site_packages_dir / "torch" / "bin"),
    ]
    env["PATH"] = os.pathsep.join(extra_paths + [env.get("PATH", "")])
    return env


def run_command(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> None:
    process = subprocess.run(command, cwd=str(cwd), env=env)
    if process.returncode != 0:
        raise RuntimeError(f"El comando falló con código {process.returncode}: {' '.join(command)}")


def basename_no_suffix(path_str: str) -> str:
    return Path(path_str).stem


def expected_liveportrait_raw_output(job: dict[str, Any], output_dir: Path) -> Path:
    return output_dir / f"{basename_no_suffix(job['source_image'])}--{basename_no_suffix(job['driving'])}.mp4"


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
    run_command(command, cwd=output_path.parent)


def render_job(job: dict[str, Any], liveportrait_root: Path, python_exe: Path, skip_audio_remux: bool, force_cpu: bool) -> Path:
    source_image = Path(job["source_image"])
    driving = Path(job["driving"])
    expected_output = Path(job["expected_output_video"])
    speech_audio = Path(job["speech_audio"]) if job.get("speech_audio") else None
    clean_env = build_clean_python_env(python_exe)

    if not source_image.exists():
        raise FileNotFoundError(f"No encontré source_image: {source_image}")
    if not driving.exists():
        raise FileNotFoundError(f"No encontré driving: {driving}")
    if speech_audio and not speech_audio.exists():
        raise FileNotFoundError(f"No encontré speech_audio: {speech_audio}")

    raw_output_dir = expected_output.parent / "liveportrait_raw"
    raw_output_dir.mkdir(parents=True, exist_ok=True)
    expected_output.parent.mkdir(parents=True, exist_ok=True)

    command = [
        str(python_exe),
        "inference.py",
        "-s",
        str(source_image),
        "-d",
        str(driving),
        "-o",
        str(raw_output_dir),
    ]
    if force_cpu:
        command.append("--flag-force-cpu")
    run_command(command, cwd=liveportrait_root, env=clean_env)

    raw_video = expected_liveportrait_raw_output(job, raw_output_dir)
    if not raw_video.exists():
        raise FileNotFoundError(f"LivePortrait no generó el archivo esperado: {raw_video}")

    if speech_audio and not skip_audio_remux:
        remux_audio(raw_video, speech_audio, expected_output)
    else:
        shutil.copy2(raw_video, expected_output)

    return expected_output


def main() -> int:
    args = parse_args()
    job_data = load_job(Path(args.job))
    jobs = job_data.get("jobs") or []
    if args.scene:
        jobs = [job for job in jobs if job.get("scene") == args.scene]
    if not jobs:
        raise RuntimeError("No hay jobs para ejecutar")

    liveportrait_root = Path(args.liveportrait_root).expanduser().resolve()
    python_exe = Path(args.python_exe).expanduser().resolve()
    if not liveportrait_root.exists():
        raise FileNotFoundError(f"No encontré el repo de LivePortrait: {liveportrait_root}")
    if not python_exe.exists():
        raise FileNotFoundError(f"No encontré el python del entorno de LivePortrait: {python_exe}")

    rendered = []
    for job in jobs:
        output_path = render_job(job, liveportrait_root, python_exe, args.skip_audio_remux, args.force_cpu)
        rendered.append(output_path)
        print(f"Render listo: {output_path}")

    print(f"Jobs completados: {len(rendered)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
