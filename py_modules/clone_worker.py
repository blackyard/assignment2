import os
import re
import shlex
import signal
import subprocess
import tempfile
import time
from typing import Dict, Optional

from progress import set_progress, is_canceled, set_canceled

# Track running clone processes keyed by task_id
_PROCS: Dict[str, subprocess.Popen] = {}

RECV_RE = re.compile(r"Receiving objects:\s+(\d+)%")
RESV_RE = re.compile(r"Resolving deltas:\s+(\d+)%")
CHK_RE = re.compile(r"Checking out files:\s+(\d+)%")


def _parse_progress(line: str) -> Optional[int]:
    for rx in (RECV_RE, RESV_RE, CHK_RE):
        m = rx.search(line)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                return None
    return None


def interruptible_clone(task_id: str, url: str, max_seconds: int = 180, depth: int = 1) -> str:
    """Clone a repo with real-time progress and cooperative cancel.

    - Writes progress updates via progress.set_progress
    - Can be canceled via progress.set_canceled() or cancel_clone()
    - Times out after max_seconds

    Returns the repo path on success, or an empty string on failure/cancel/timeout.
    """
    if not url or "github.com" not in url:
        set_progress(task_id, "error", 100, {"message": "Invalid GitHub URL"})
        return ""

    try:
        temp_dir = tempfile.mkdtemp()
        repo_name = url.rstrip("/").split("/")[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
        repo_path = os.path.join(temp_dir, repo_name)

        cmd = [
            "git", "clone", "--progress", f"--depth={depth}", url, repo_path
        ]
        # Start process
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )
        _PROCS[task_id] = proc
        start = time.time()
        set_progress(task_id, "cloning", 20, {"stage": "clone"})

        # Stream stderr for progress
        try:
            while True:
                if is_canceled(task_id):
                    set_canceled(task_id, "Canceled by user")
                    try:
                        proc.terminate()
                    except Exception:
                        pass
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    return ""

                if (time.time() - start) > max_seconds:
                    set_progress(task_id, "timeout", 100, {"message": "Clone timed out"})
                    try:
                        proc.terminate()
                    except Exception:
                        pass
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    return ""

                # Non-blocking read of a line from stderr
                if proc.stderr is None:
                    break
                line = proc.stderr.readline()
                if not line:
                    # If process ended, break; otherwise short sleep and continue
                    if proc.poll() is not None:
                        break
                    time.sleep(0.1)
                    continue

                p = _parse_progress(line)
                if p is not None:
                    # map 20-80% to clone progress
                    mapped = 20 + int(0.6 * p)
                    set_progress(task_id, "cloning", mapped, {"stage": "clone"})

            code = proc.wait(timeout=5)
        finally:
            _PROCS.pop(task_id, None)

        if code == 0:
            set_progress(task_id, "mapped", 60, {"stage": "map"})
            return repo_path
        else:
            set_progress(task_id, "error", 100, {"message": f"git clone failed: {code}"})
            return ""

    except FileNotFoundError:
        set_progress(task_id, "error", 100, {"message": "git not found in PATH"})
        return ""
    except Exception as e:
        set_progress(task_id, "error", 100, {"message": str(e)})
        return ""


def cancel_clone(task_id: str) -> bool:
    p = _PROCS.get(task_id)
    if not p:
        # Already finished or never started
        set_canceled(task_id, "No running process")
        return False
    try:
        p.terminate()
    except Exception:
        pass
    try:
        p.kill()
    except Exception:
        pass
    set_canceled(task_id, "Canceled by user")
    _PROCS.pop(task_id, None)
    return True
