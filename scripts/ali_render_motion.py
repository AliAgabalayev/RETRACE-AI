#!/usr/bin/env python3
"""Render the presentation evidence walkthrough; never call an inference provider."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


REPO = Path(__file__).resolve().parents[1]
FINAL_SHA = "79a0ef740196cbaa0639579386c6c591d2bfd8ca"
CONFIG_HASH = "eaa371255716"
WIDTH, HEIGHT, FPS = 1920, 1080, 30
TOTAL_SECONDS = 110
FONT = Path("/usr/share/fonts/google-noto/NotoSans-Regular.ttf")


@dataclass(frozen=True)
class Scene:
    asset: str
    seconds: int
    source: str
    narration: str


SCENES = (
    Scene(
        "01_problem.png", 13,
        "Source: PROJECT_BRIEF | illustrative problem framing",
        "Oyun screenshot-larında hər fərq bug deyil. İşıq və görünüş dəyişə bilər; "
        "amma mövcud obyektin yoxa çıxması qaydanı poza bilər. Məqsədimiz fərqi "
        "tapmaq və qaydaya əsaslanan qərarı visual evidence ilə göstərməkdir.",
    ),
    Scene(
        "02_flow.png", 16,
        "Source: frozen implementation 79a0ef7 | config eaa371255716",
        "Reference, candidate və allow-deny rules daxil olur. Frozen DINOv2 və "
        "pixel diff dəyişiklik bölgələrini təklif edir. VLM bölgəni təsvir edib "
        "qaydanı tətbiq edir; whole-scene audit-dən sonra deterministic policy "
        "PASS, FAIL və ya NEEDS REVIEW qaytarır.",
    ),
    Scene(
        "03_barrel.png", 17,
        "Source: vr_4b921c5d | C2 saved evidence + Qwen A1 baseline",
        "Bu real development pair-də barrel yox olur. Qwen nəticəsi REVIEW idi. "
        "Eyni pipeline-da OpenRouter Gemini saxlanmış C2 nəticəsində D1 üzrə "
        "FAIL verdi. Burada əvvəlcədən yaradılmış evidence göstərilir; bu video "
        "yeni live inference deyil.",
    ),
    Scene(
        "04_results.png", 22,
        "Source: C2 B/C predictions.jsonl | 12 development pairs",
        "On iki development pair üzrə Gemini full-frame B və hybrid C hər ikisi "
        "bir PASS, dörd FAIL, yeddi REVIEW verdi: coverage beş bölü on iki. "
        "Bug false-PASS hər ikisində bir bölü beşdir. C-də üç bug düzgün FAIL, "
        "bir clean pair səhv FAIL; B-də iki bug düzgün FAIL və iki clean pair "
        "səhv FAIL. Yekun sayların bərabərliyi DINOv2 üstünlüyünü göstərmir.",
    ),
    Scene(
        "05_failure.png", 20,
        "Source: vr_c1f47c57 | C2 false-PASS in B and C",
        "Əsas failure budur: reference-dəki stone pedestal candidate-də yoxdur, "
        "amma həm B, həm C PASS verib. Buna görə beş bölü on iki coverage ilə "
        "bir bölü beş bug false-PASS birlikdə göstərilir. Nəticələri etibarlı "
        "production detector və ya workload azalması kimi təqdim etmirik.",
    ),
    Scene(
        "06_evidence.png", 12,
        "Source: C2 call/cost records + ZIP verification records | offline",
        "Evidence ZIP input-ları, rules, crops, analysis və evidence JSON-u "
        "saxlayır. C2 B və C birlikdə səksən fresh call, sıfır retry edir; "
        "iki arm üzrə provider-reported total cost təxminən iyirmi doqquz "
        "sentdir. Saved evidence ilə final UI replay "
        "verification ayrıca mərhələlərdir.",
    ),
    Scene(
        "07_next.png", 10,
        "Source: project limitations | final UI recording pending",
        "Bu, on iki pair üzrə development diagnostic-dir. Labels model "
        "output-ları başlayandan sonra tamamlanıb; beş bug label-dan dördü "
        "Claude təklifi olub, Ali təsdiqləyib. Növbəti addım müstəqil "
        "pre-labelled data və proposal ablation-dur.",
    ),
)


def run(command: list[str], *, log: Path | None = None) -> str:
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False)
    if log is not None:
        log.write_text(result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{command[0]} failed ({result.returncode}):\n"
                           f"{result.stderr[-4000:]}")
    return result.stdout


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def timestamp(seconds: int) -> str:
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def srt_timestamp(seconds: int) -> str:
    return f"00:{seconds // 60:02d}:{seconds % 60:02d},000"


def filter_path(path: Path) -> str:
    # FFmpeg filter paths use their own escaping, independent of subprocess argv.
    return str(path).replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def label_filter(path: Path, *, x: str, y: int, color: str = "0xEAF0F7",
                 size: int = 21) -> str:
    return (f"drawtext=fontfile='{filter_path(FONT)}':"
            f"textfile='{filter_path(path)}':expansion=none:"
            f"fontcolor={color}:fontsize={size}:x={x}:y={y}")


def prepare_labels(output: Path, scene: Scene, index: int, start: int) -> list[Path]:
    texts = (
        "PRERECORDED / EVIDENCE WALKTHROUGH",
        "DRAFT / UI RECORDING PENDING",
        scene.source,
        f"{index:02d}/07   {timestamp(start)} - {timestamp(start + scene.seconds)}",
    )
    paths = []
    for role, text in zip(("mode", "draft", "source", "chapter"), texts):
        path = output / f"scene_{index:02d}_{role}.txt"
        path.write_text(text, encoding="utf-8")
        paths.append(path)
    return paths


def scene_filters(output: Path, scene: Scene, index: int, start: int) -> str:
    mode, draft, source, chapter = prepare_labels(output, scene, index, start)
    effects = [
        label_filter(mode, x="48", y=16, color="0x7DE1CD", size=22),
        label_filter(draft, x="w-tw-48", y=16, color="0xF5C676", size=22),
        label_filter(source, x="48", y=1034, size=20),
        label_filter(chapter, x="w-tw-48", y=1034, size=20),
    ]
    return (
        f"[0:v]scale={WIDTH}:976:force_original_aspect_ratio=decrease:"
        "force_divisible_by=2:flags=lanczos,"
        f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:54:color=0x08111E,"
        "setsar=1,format=yuv420p,"
        "fade=t=in:st=0:d=0.30:color=0x08111E,"
        f"fade=t=out:st={scene.seconds - 0.30:.2f}:d=0.30:color=0x08111E,"
        "drawbox=x=0:y=0:w=iw:h=54:color=0x08111E:t=fill,"
        "drawbox=x=0:y=1030:w=iw:h=50:color=0x08111E:t=fill,"
        + ",".join(effects) + "[framed];"
        "[1:v]format=yuv420p[progress];"
        "[framed][progress]overlay="
        f"x='-W+W*min(1,(t+{start})/{TOTAL_SECONDS})':y=1076:"
        "shortest=1:format=yuv420[out]"
    )


def verify_video(path: Path) -> dict:
    probe = json.loads(run([
        "ffprobe", "-v", "error", "-show_entries",
        "stream=codec_name,codec_type,width,height,r_frame_rate:format=duration,size",
        "-of", "json", str(path),
    ]))
    videos = [stream for stream in probe["streams"]
              if stream["codec_type"] == "video"]
    if len(videos) != 1:
        raise RuntimeError(f"Expected one video stream: {probe}")
    video = videos[0]
    if (video["codec_name"], video["width"], video["height"]) != (
        "h264", WIDTH, HEIGHT
    ):
        raise RuntimeError(f"Unexpected format: {probe}")
    if abs(float(probe["format"]["duration"]) - TOTAL_SECONDS) > 0.05:
        raise RuntimeError(f"Unexpected duration: {probe}")
    if any(stream["codec_type"] == "audio" for stream in probe["streams"]):
        raise RuntimeError("Draft must be silent; unexpected audio stream")
    return probe


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, default=REPO / "docs/ali/pitch")
    parser.add_argument("--output", type=Path, default=REPO / "artifacts/ali/motion")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--reuse-unchanged", action="store_true",
                        help="Reuse existing segments with the same asset, timing and caption")
    args = parser.parse_args()
    assets, output = args.assets.resolve(), args.output.resolve()
    permitted = (REPO / "artifacts/ali/motion").resolve()
    if not output.is_relative_to(permitted):
        raise SystemExit(f"Output must be within {permitted}")
    if sum(scene.seconds for scene in SCENES) != TOTAL_SECONDS:
        raise SystemExit("Scene durations must add up to 110 seconds")
    for program in ("ffmpeg", "ffprobe"):
        if shutil.which(program) is None:
            raise SystemExit(f"Missing existing tool: {program}; no install attempted")
    if not FONT.is_file():
        raise SystemExit(f"Font missing: {FONT}")
    missing = [str(assets / scene.asset) for scene in SCENES
               if not (assets / scene.asset).is_file()]
    if missing:
        raise SystemExit("Deck PNG assets pending:\n" + "\n".join(missing))
    output.mkdir(parents=True, exist_ok=True)

    prior_scenes = {}
    prior_manifest = output / "motion_manifest.json"
    if args.reuse_unchanged and prior_manifest.is_file():
        prior = json.loads(prior_manifest.read_text(encoding="utf-8"))
        prior_scenes = {row["index"]: row for row in prior.get("scenes", [])}

    segments, storyboard, guide = [], [], []
    start = 0
    for index, scene in enumerate(SCENES, 1):
        asset = assets / scene.asset
        asset_hash = checksum(asset)
        print(f"[{index}/7] {scene.asset}: {start}-{start + scene.seconds} s",
              flush=True)
        segment = output / f"scene_{index:02d}.mp4"
        command = [
            "ffmpeg", "-hide_banner", "-y", "-loglevel", "warning",
            "-filter_complex_threads", "1", "-loop", "1", "-framerate", str(FPS),
            "-i", str(asset), "-f", "lavfi", "-i",
            f"color=c=0x7DE1CD:s={WIDTH}x4:r={FPS}",
            "-filter_complex", scene_filters(output, scene, index, start),
            "-map", "[out]", "-t", str(scene.seconds), "-r", str(FPS), "-an",
            "-c:v", "libx264", "-threads", str(args.threads), "-preset", "fast",
            "-tune", "stillimage", "-crf", "20", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", str(segment),
        ]
        prior = prior_scenes.get(index, {})
        reuse = (segment.is_file() and prior.get("asset_sha256") == asset_hash
                 and prior.get("start_s") == start
                 and prior.get("end_s") == start + scene.seconds
                 and prior.get("source_caption") == scene.source)
        if reuse:
            print("  Reusing unchanged presentation segment", flush=True)
        else:
            run(command, log=output / f"scene_{index:02d}.log")
            if checksum(asset) != asset_hash:
                raise RuntimeError(f"Asset changed during rendering: {asset}; rerun render")
        segments.append(segment)
        storyboard.append({
            "index": index, "start_s": start, "end_s": start + scene.seconds,
            "asset": str(asset.relative_to(REPO)), "asset_sha256": asset_hash,
            "source_caption": scene.source, "presentation_mode": "PRERECORDED",
        })
        guide.append(f"{index}\n{srt_timestamp(start)} --> "
                     f"{srt_timestamp(start + scene.seconds)}\n{scene.narration}\n")
        start += scene.seconds

    concat = output / "concat.txt"
    concat.write_text("".join(f"file '{segment.name}'\n" for segment in segments),
                      encoding="utf-8")
    movie = output / "ali_evidence_motion_DRAFT_110s.mp4"
    print("Concatenating and verifying draft...", flush=True)
    run([
        "ffmpeg", "-hide_banner", "-y", "-loglevel", "warning", "-f", "concat",
        "-safe", "1", "-i", str(concat), "-c", "copy", "-an",
        "-movflags", "+faststart", "-metadata", "title=AI Gaming evidence walkthrough DRAFT",
        "-metadata", "comment=Prerecorded evidence walkthrough; UI recording pending; "
        f"code {FINAL_SHA}; config {CONFIG_HASH}", str(movie),
    ], log=output / "concat.log")
    probe = verify_video(movie)
    (output / "narration_guide_AZ.srt").write_text("\n".join(guide), encoding="utf-8")
    (output / "motion_manifest.json").write_text(json.dumps({
        "status": "DRAFT_UI_RECORDING_PENDING", "silent": True,
        "final_code_sha": FINAL_SHA, "frozen_config_hash": CONFIG_HASH,
        "runtime": "OpenRouter / google/gemini-3.5-flash / reasoning low / prompt v9",
        "c2_cost_scope": "B and C combined: 80 fresh calls, 0 retries, USD 0.2871945",
        "inference_called_by_renderer": False,
        "mode": "PRERECORDED_EVIDENCE_WALKTHROUGH", "duration_s": TOTAL_SECONDS,
        "video": movie.name, "video_sha256": checksum(movie), "probe": probe,
        "scenes": storyboard,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for index, scene in enumerate(storyboard, 1):
        position = (scene["start_s"] + scene["end_s"]) / 2
        run([
            "ffmpeg", "-hide_banner", "-y", "-loglevel", "warning", "-ss", str(position),
            "-i", str(movie), "-frames:v", "1", "-update", "1",
            str(output / f"preview_{index:02d}.png"),
        ])
    print(json.dumps({"video": str(movie), "duration_s": TOTAL_SECONDS,
                      "codec": "h264", "size": "1920x1080", "silent": True}),
          flush=True)


if __name__ == "__main__":
    main()
