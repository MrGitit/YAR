import re, srt
from datetime import timedelta
from pathlib import Path
def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\\s+", text.strip()); return [p for p in parts if p]
def script_to_srt(script: str, audio_duration_sec: float, out_path: Path) -> Path:
    sents = split_sentences(script); total=max(1,sum(len(s.split()) for s in sents))
    subs=[]; t=0.0
    for i,s in enumerate(sents,1):
        w=max(1,len(s.split())); dur=audio_duration_sec*(w/total)
        subs.append(srt.Subtitle(index=i,start=timedelta(seconds=t),end=timedelta(seconds=min(t+dur,audio_duration_sec)),content=s))
        t+=dur
    out=Path(out_path); out.write_text(srt.compose(subs),encoding="utf-8"); return out
