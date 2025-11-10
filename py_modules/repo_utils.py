import os
import tempfile
import git
from urllib.parse import urlparse

EXCLUDE_DIRS = {'.git', 'node_modules', '__pycache__'}


def is_valid_github_url(url: str) -> bool:
    """Conservative GitHub repo URL validator.

    - Accepts http/https schemes
    - Host must contain github.com (case-insensitive)
    - Path should have at least /owner/repo (allows extra segments)
    """
    try:
        parsed = urlparse((url or "").strip())
        if parsed.scheme not in {"http", "https"}:
            return False
        host = (parsed.netloc or "").lower()
        if "github.com" not in host:
            return False
        parts = [seg for seg in (parsed.path or "").strip("/").split("/") if seg]
        if len(parts) < 2:
            return False
        return True
    except Exception:
        return False


def clone_repo(url: str) -> str:
    """Clone a GitHub repo to a temporary directory and return the path.

    Uses a shallow clone (depth=1) for speed and bandwidth. Returns an empty
    string on failure.
    """
    if not is_valid_github_url(url):
        print("Invalid GitHub URL.")
        return ""

    try:
        temp_dir = tempfile.mkdtemp()
        # Normalize repo name (strip trailing .git if present)
        repo_name = url.rstrip('/').split('/')[-1]
        if repo_name.endswith('.git'):
            repo_name = repo_name[:-4]
        repo_path = os.path.join(temp_dir, repo_name)
        # Shallow clone for speed
        git.Repo.clone_from(url, repo_path, multi_options=["--depth", "1"])
        return repo_path
    except Exception as e:
        print(f"Clone failed: {e}")
        return ""


def generate_file_tree(repo_path: str) -> dict:
    tree = {}

    for root, dirs, files in os.walk(repo_path):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        rel_path = os.path.relpath(root, repo_path)
        subtree = tree
        if rel_path != ".":
            for part in rel_path.split(os.sep):
                subtree = subtree.setdefault(part, {})
        subtree["_files"] = files

    return tree


def flatten_tree(repo_path: str, tree: dict) -> list:
    """Flatten a file tree dict (as produced by generate_file_tree) into
    a list of file path dicts with relative and absolute paths.

    Returns: [{"rel": "path/inside/repo.py", "abs": "C:/.../repo/path/inside/repo.py"}, ...]
    """
    files = []

    def walk(subtree: dict, prefix_parts: list):
        # files under current subtree
        for fname in subtree.get("_files", []):
            rel = os.path.join(*(prefix_parts + [fname])) if prefix_parts else fname
            files.append({
                "rel": rel,
                "abs": os.path.join(repo_path, rel),
            })
        # recurse into directories
        for name, child in subtree.items():
            if name == "_files":
                continue
            walk(child, prefix_parts + [name])

    walk(tree or {}, [])
    return files


def summarize_readme(repo_path: str) -> str:
    readme_path = os.path.join(repo_path, "README.md")
    if not os.path.exists(readme_path):
        return "No README.md found."

    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Simple summary: first few lines
        return "\n".join(content.strip().splitlines()[:10])
    except Exception as e:
        return f"Error reading README: {e}"