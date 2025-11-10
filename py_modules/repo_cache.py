import os
import json
import hashlib
import shutil
import subprocess
import time
from typing import Optional

from progress import set_progress, is_canceled, set_canceled

CACHE_ROOT = os.path.join("outputs", "cache")
os.makedirs(CACHE_ROOT, exist_ok=True)


def _key(url: str) -> str:
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    name = url.rstrip("/").split("/")[-1]
    if name.endswith(".git"):
        name = name[:-4]
    safe = "".join(c for c in name if c.isalnum() or c in ("-", "_"))
    return f"{safe}-{h}"


def get_cached_path(url: str) -> Optional[str]:
    path = os.path.join(CACHE_ROOT, _key(url))
    if os.path.exists(path) and os.path.isdir(path) and os.path.exists(os.path.join(path, ".git")):
        return path
    return None


def invalidate_cache(url: str) -> None:
    p = get_cached_path(url)
    if p and os.path.exists(p):
        try:
            shutil.rmtree(p, ignore_errors=True)
        except Exception:
            pass


def ensure_cached_repo(task_id: str, url: str, refresh: bool = False, timeout: int = 180, depth: int = 1) -> str:
    """Ensure a persistent cached clone exists and return its path.

    If refresh=True or cache missing, perform a git clone into outputs/cache/<key> with
    --depth and --progress, supporting cancel and timeout.
    """
    if not url or "github.com" not in url:
        set_progress(task_id, "error", 100, {"stage": "cache", "message": "Invalid GitHub URL"})
        return ""

    cache_path = os.path.join(CACHE_ROOT, _key(url))
    if not refresh:
        p = get_cached_path(url)
        if p:
            # Cache hit
            set_progress(task_id, "cache", 25, {"stage": "cache", "cached": True})
            return p

    # (Re)clone into cache_path
    try:
        # Clean any existing folder if refreshing
        if os.path.exists(cache_path):
            shutil.rmtree(cache_path, ignore_errors=True)
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)

        # Ensure git is available
        if shutil.which("git") is None:
            set_progress(task_id, "error", 100, {"stage": "cache", "message": "git not found in PATH"})
            return ""

        cmd = ["git", "clone", "--progress", f"--depth={depth}", url, cache_path]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        start = time.time()
        set_progress(task_id, "cache", 15, {"stage": "cache", "action": "cloning"})

        while True:
            if is_canceled(task_id):
                set_canceled(task_id, "Canceled during cache")
                try:
                    proc.terminate()
                except Exception:
                    pass
                try:
                    proc.kill()
                except Exception:
                    pass
                return ""
            if (time.time() - start) > timeout:
                set_progress(task_id, "timeout", 100, {"message": "Cache clone timed out"})
                try:
                    proc.terminate()
                except Exception:
                    pass
                try:
                    proc.kill()
                except Exception:
                    pass
                return ""
            if proc.stderr is None:
                break
            line = proc.stderr.readline()
            if not line:
                if proc.poll() is not None:
                    break
                time.sleep(0.1)
                continue
            # We could parse % here for finer progress; keep simple to avoid duplication
        code = proc.wait(timeout=5)
        if code == 0:
            set_progress(task_id, "cache", 25, {"stage": "cache"})
            return cache_path
        # Non-zero exit; surface an error message
        try:
            _, err = proc.communicate(timeout=1)
        except Exception:
            err = ""
        set_progress(task_id, "error", 100, {"stage": "cache", "message": f"git clone failed: {code}", "stderr": (err or "").splitlines()[-5:]})
        return ""
    except FileNotFoundError:
        set_progress(task_id, "error", 100, {"stage": "cache", "message": "git not found in PATH"})
        return ""
    except Exception as e:
        set_progress(task_id, "error", 100, {"stage": "cache", "message": str(e)})
        return ""