import subprocess
from pathlib import Path
from .utils import getenv
import pyttsx3
def tts_to_file(text: str, out_wav: Path) -> Path:
    out_wav = Path(out_wav); out_wav.parent.mkdir(parents=True, exist_ok=True)
    if getenv("TTS_ENGINE","mimic3").lower()=="mimic3":
        voice = getenv("MIMIC3_VOICE","en_US/vctk_low")
        bin = getenv("MIMIC3_BIN","mimic3")
        if subprocess.run([bin,"--voice",voice,"-o",str(out_wav),text]).returncode!=0:
            raise RuntimeError("Mimic3 TTS failed")
        return out_wav
    eng = pyttsx3.init(); eng.save_to_file(text, str(out_wav)); eng.runAndWait(); return out_wav
