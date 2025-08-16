from PIL import Image as _PILImage
# Pillow >=10 removed ANTIALIAS; MoviePy 1.0.3 still references it.
if not hasattr(_PILImage, "ANTIALIAS"):
    try:
        _PILImage.ANTIALIAS = _PILImage.Resampling.LANCZOS
    except Exception:
        pass

from pathlib import Path
from typing import List
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

def ken_burns(image: Path, duration: float, zoom: float = 1.07) -> ImageClip:
    clip = ImageClip(str(image)).set_duration(duration)
    def scaler(t): return 1 + (zoom - 1) * (t / duration)
    return clip.resize(lambda t: scaler(t)).set_position("center")

def build_video(images: List[Path], per_scene_durations: List[float], narration_wav: Path, fps: int = 30, crossfade: float = 0.25, out_path: Path | None = None) -> Path:
    clips = [ken_burns(img, dur) for img, dur in zip(images, per_scene_durations)]
    clips = [clips[0]] + [c.crossfadein(crossfade) for c in clips[1:]]
    video = concatenate_videoclips(clips, method="compose")
    audio = AudioFileClip(str(narration_wav))
    video = video.set_audio(audio).set_fps(fps)
    final = video.subclip(0, audio.duration)
    out = Path(out_path or "output/exports/final.mp4"); out.parent.mkdir(parents=True, exist_ok=True)
    final.write_videofile(str(out), codec="libx264", audio_codec="aac"); return out
