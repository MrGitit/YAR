from PIL import Image as _PILImage
if not hasattr(_PILImage, "ANTIALIAS"):
    try:
        _PILImage.ANTIALIAS = _PILImage.Resampling.LANCZOS
    except Exception:
        pass

from pathlib import Path
from typing import List
from moviepy.editor import ImageClip, AudioFileClip, ImageSequenceClip, concatenate_videoclips
from moviepy.video.fx.all import speedx

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

def build_video_from_frame_sequences(frame_sequences: List[List[Path]], per_scene_durations: List[float], narration_wav: Path, fps: int = 24, crossfade: float = 0.25, out_path: Path | None = None) -> Path:
    assert len(frame_sequences) == len(per_scene_durations)
    scene_clips = []
    for frames, target_dur in zip(frame_sequences, per_scene_durations):
        seq = ImageSequenceClip([str(p) for p in frames], fps=fps)
        if abs(seq.duration - target_dur) > 0.05:
            seq = seq.fx(speedx, seq.duration / max(0.05, target_dur))
        scene_clips.append(seq)
    clips = [scene_clips[0]] + [c.crossfadein(crossfade) for c in scene_clips[1:]]
    video = concatenate_videoclips(clips, method="compose")
    audio = AudioFileClip(str(narration_wav))
    video = video.set_audio(audio).set_fps(fps)
    final = video.subclip(0, audio.duration)
    out = Path(out_path or "output/exports/final_ad.mp4"); out.parent.mkdir(parents=True, exist_ok=True)
    final.write_videofile(str(out), codec="libx264", audio_codec="aac"); return out
