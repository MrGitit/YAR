import argparse, math
from pathlib import Path
from rich import print
from dotenv import load_dotenv
from moviepy.editor import AudioFileClip
from .utils import getenv, ensure_dir
from .llm import generate_script_from_article
from .comfy_client import ComfyClient
from .tts import tts_to_file
from .video_editor import build_video
from .captions import script_to_srt

def naive_scene_prompts(script: str, n: int) -> list[str]:
    paras=[p.strip() for p in script.split("\n") if p.strip()]
    if len(paras)<n:
        text=" ".join(paras) if paras else script
        words=text.split(); size=math.ceil(len(words)/n)
        parts=[" ".join(words[i:i+size]) for i in range(0,len(words),size)]
    else:
        parts=paras[:n]
    base=("cinematic, newsroom b-roll, volumetric light, detailed, ui hud overlays, 9:16 composition")
    prompts=[]
    for chunk in parts:
        toks=[t.strip(',.!?').lower() for t in chunk.split() if len(t)>3]
        kws=", ".join(list(dict.fromkeys(toks))[:6])
        prompts.append(f"{base}, keywords: {kws}")
    return prompts

def main():
    load_dotenv()
    ap=argparse.ArgumentParser()
    ap.add_argument("--script_path")
    ap.add_argument("--summary")
    ap.add_argument("--scenes",type=int,default=int(getenv("MAX_SCENES","5") or 5))
    ap.add_argument("--mode",choices=["stills","motion"],default="stills")
    ap.add_argument("--out",default=getenv("OUTPUT_DIR","output/exports")+"/yar_demo.mp4")
    args=ap.parse_args()

    ensure_dir(getenv("OUTPUT_DIR","output/exports"))

    if args.script_path:
        script_text=Path(args.script_path).read_text(encoding="utf-8")
    elif args.summary:
        script_text=generate_script_from_article(args.summary)
        Path("output/script.generated.txt").write_text(script_text,encoding="utf-8")
    else:
        script_text=Path("samples/script.txt").read_text(encoding="utf-8")
    print("[cyan]Script:[/cyan]\n",script_text)

    narration=Path(getenv("OUTPUT_DIR","output/exports"))/"narration.wav"
    tts_to_file(script_text, narration)

    audio=AudioFileClip(str(narration)); total=audio.duration
    per_scene=[total/args.scenes]*args.scenes
    prompts=naive_scene_prompts(script_text,args.scenes)

    client=ComfyClient()
    w=int(getenv("IMAGE_WIDTH","1080")); h=int(getenv("IMAGE_HEIGHT","1920"))
    steps=int(getenv("STEPS","28")); seed=int(getenv("SEED","123456"))
    neg=getenv("NEGATIVE_PROMPT","lowres, watermark, logo, text, blurry, jpeg artifacts")

    if args.mode=="motion":
        print("[yellow]Motion mode is not wired yet — falling back to stills.[/yellow]")

    images=[]
    for i,p in enumerate(prompts,1):
        images.append(client.generate_image(p,f"yar_scene_{i:02d}",seed+i,steps,w,h,neg))

    out=build_video(images,per_scene,narration,
                    fps=int(getenv("FPS","30")),
                    crossfade=float(getenv("CROSSFADE_SECONDS","0.25")),
                    out_path=Path(args.out))

    srtp=Path(args.out).with_suffix(".srt"); script_to_srt(script_text,total,srtp)
    print(f"\n[bold green]DONE[/bold green] → {out}"); print(f"Captions → {srtp}")
    print("Burn-in captions (optional):")
    print(f"ffmpeg -i {out} -vf \"subtitles={srtp}\" -c:a copy {out.with_name(out.stem+'_sub.mp4')}")
if __name__=="__main__": main()
