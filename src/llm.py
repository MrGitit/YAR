import httpx
from .utils import getenv
def generate_script_from_article(summary: str) -> str:
    base = getenv("OLLAMA_BASE_URL","http://127.0.0.1:11434")
    model = getenv("OLLAMA_MODEL","mistral")
    system = ("You are a concise news writer. Create a 45–55 second YouTube Shorts script: "
              "1-line hook, 3–4 crisp facts in plain English, 1-line outro. Neutral tone. "
              "Cite source once with 'According to ...'. ~120 words total.")
    prompt = f"{system}\n\nArticle summary:\n{summary}\n\nReturn only the script."
    with httpx.Client(timeout=60.0) as c:
        r = c.post(f"{base}/api/generate", json={"model":model,"prompt":prompt,"stream":False}); r.raise_for_status()
        return r.json().get("response","").strip()
