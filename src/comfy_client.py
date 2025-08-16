import json, time
from pathlib import Path
import requests
from .utils import getenv

class ComfyClient:
    def __init__(self, server_url: str | None = None):
        self.server_url = server_url or getenv("COMFYUI_SERVER_URL","http://127.0.0.1:8188")
        self.output_dir = getenv("COMFYUI_OUTPUT_DIR","")

    def _load(self, path):
        return json.load(open(path, "r", encoding="utf-8"))

    def generate_image(self, prompt, filename_prefix, seed, steps, width, height, negative_prompt):
        wf = self._load("comfy/workflow_sdxl_keyframe.json")
        for n in wf.values():
            t=n["class_type"]
            if t=="CheckpointLoaderSimple": n["inputs"]["ckpt_name"]=getenv("SDXL_CHECKPOINT","sd_xl_base_1.0.safetensors")
            elif t=="CLIPTextEncode":
                if n["inputs"]["text"]=="__POS_PROMPT__": n["inputs"]["text"]=prompt
                elif n["inputs"]["text"]=="__NEG_PROMPT__": n["inputs"]["text"]=negative_prompt
            elif t=="EmptyLatentImage": n["inputs"]["width"]=width; n["inputs"]["height"]=height
            elif t=="KSampler": n["inputs"]["seed"]=seed; n["inputs"]["steps"]=steps
            elif t=="SaveImage": n["inputs"]["filename_prefix"]=filename_prefix
        r = requests.post(f"{self.server_url}/prompt", json={"prompt":wf,"client_id":"yar"}, timeout=60); r.raise_for_status()
        pid = r.json().get("prompt_id"); img_path=None
        for _ in range(600):
            time.sleep(1)
            h = requests.get(f"{self.server_url}/history/{pid}")
            if h.status_code!=200: continue
            data = h.json().get(pid,{}).get("outputs",{})
            for o in data.values():
                if "images" in o and o["images"]:
                    info=o["images"][0]; fn=info["filename"]; sub=info.get("subfolder","")
                    base=Path(self.output_dir) if self.output_dir else Path("ComfyUI/output")
                    img_path = base/sub/fn; break
            if img_path: break
        if not img_path: raise RuntimeError("ComfyUI did not return an image in time.")
        return img_path

    def generate_ad_frames(self, prompt, filename_prefix, seed, steps, width, height, negative_prompt, motion_model, strength, num_frames, fps):
        wf = self._load("comfy/workflow_animatediff.json")
        for n in wf.values():
            t=n["class_type"]
            if t=="CheckpointLoaderSimple": n["inputs"]["ckpt_name"]=getenv("SDXL_CHECKPOINT","sd_xl_base_1.0.safetensors")
            elif t=="CLIPTextEncode":
                v=n["inputs"]["text"]
                if v=="__POS_PROMPT__": n["inputs"]["text"]=prompt
                elif v=="__NEG_PROMPT__": n["inputs"]["text"]=negative_prompt
            elif t=="EmptyLatentImage": n["inputs"]["width"]=width; n["inputs"]["height"]=height
            elif t=="ADE_LoadMM": n["inputs"]["motion_module"]=motion_model
            elif t=="ADE_Apply": n["inputs"]["strength"]=strength
            elif t=="KSampler": n["inputs"]["seed"]=seed; n["inputs"]["steps"]=steps
            elif t=="SaveImage": n["inputs"]["filename_prefix"]=filename_prefix

        out_dir = Path(self.output_dir or "ComfyUI/output"); frames=[]
        for i in range(num_frames):
            wf_i = json.loads(json.dumps(wf))
            for n in wf_i.values():
                if n["class_type"]=="KSampler": n["inputs"]["seed"]=int(seed)+i
            r = requests.post(f"{self.server_url}/prompt", json={"prompt":wf_i,"client_id":"yar_ad"}, timeout=60); r.raise_for_status()
            pid = r.json().get("prompt_id"); saved=None
            for _ in range(120):
                time.sleep(0.5)
                h = requests.get(f"{self.server_url}/history/{pid}")
                if h.status_code!=200: continue
                data = h.json().get(pid,{}).get("outputs",{})
                for o in data.values():
                    if "images" in o and o["images"]:
                        info=o["images"][0]; fn=info["filename"]; sub=info.get("subfolder","")
                        saved = out_dir/sub/fn; break
                if saved: break
            if not saved: raise RuntimeError("AnimateDiff did not return a frame in time.")
            frames.append(saved)
        return frames
