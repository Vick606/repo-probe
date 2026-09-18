"""Clone a GitHub repository at a specific ref (tag, branch, or commit SHA)."""

import subprocess
import sys
import tempfile
from pathlib import Path


def clone_repo(repo_url: str, ref: str, dest: Path) -> Path:
    """Clone repo_url and checkout ref. Returns the path to the cloned repo.

    Raises FileExistsError if dest already exists and is not empty.
    Raises subprocess.CalledProcessError if git clone or checkout fails.
    """
    dest = Path(dest)
    if dest.exists() and any(dest.iterdir()):
        raise FileExistsError(f"Destination already exists and is not empty: {dest}")

    subprocess.run(
        ["git", "clone", "--quiet", repo_url, str(dest)],
        check=True,
    )
    subprocess.run(
        ["git", "checkout", "--quiet", ref],
        cwd=dest,
        check=True,
    )
    return dest


def _head_commit(repo_path: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m repo_probe.cloner <repo_url> <ref>")
        sys.exit(1)

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "repo"
        clone_repo(sys.argv[1], sys.argv[2], path)
        print(f"Cloned to: {path}")
        print(f"HEAD commit: {_head_commit(path)}")
        print("Top-level contents:")
        for item in sorted(path.iterdir()):
            print(f"  {item.name}")