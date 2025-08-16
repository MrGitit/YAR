import os
from dotenv import load_dotenv
load_dotenv()
def getenv(key: str, default: str = "") -> str: return os.getenv(key, default)
def ensure_dir(path: str) -> None: os.makedirs(path, exist_ok=True)
