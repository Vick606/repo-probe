"""Generate a Dockerfile from a TestSetup and build the image."""

import json
import subprocess
import sys
from pathlib import Path

from repo_probe.detector import TestSetup, detect_test_setup


_RUNNER_PACKAGES: dict[str, str | None] = {
    "pytest": "pytest",
    "unittest": None,  # stdlib, nothing to install
    "tox": "tox",
    "nox": "nox",
}


def render_dockerfile(setup: TestSetup, python_version: str = "3.12") -> str:
    """Return Dockerfile content for the given test setup."""
    lines = [
        f"FROM python:{python_version}-slim",
        "",
        "WORKDIR /app",
        "COPY . .",
        "",
        "# Install the project if it has packaging metadata.",
        "RUN if [ -f pyproject.toml ] || [ -f setup.py ]; then \\",
        '        pip install --no-cache-dir -e ".[test]" 2>/dev/null || \\',
        "        pip install --no-cache-dir -e . ; \\",
        "    fi",
    ]

    pkg = _RUNNER_PACKAGES.get(setup.runner)
    if pkg:
        lines.append(f"RUN pip install --no-cache-dir {pkg}")

    lines.append("")
    lines.append(f"CMD {json.dumps(setup.command)}")
    lines.append("")
    return "\n".join(lines)


def build_image(
    repo_path: Path,
    setup: TestSetup,
    tag: str,
    dockerfile_dir: Path | None = None,
    python_version: str = "3.12",
) -> Path:
    """Write a Dockerfile and build the image. Returns the Dockerfile path."""
    repo_path = Path(repo_path)
    if dockerfile_dir is None:
        dockerfile_dir = repo_path.parent
    dockerfile_dir = Path(dockerfile_dir)
    dockerfile_dir.mkdir(parents=True, exist_ok=True)

    safe_name = tag.replace(":", "_").replace("/", "_")
    dockerfile = dockerfile_dir / f"Dockerfile.{safe_name}"
    dockerfile.write_text(render_dockerfile(setup, python_version), encoding="utf-8")

    subprocess.run(
        ["docker", "build", "-t", tag, "-f", str(dockerfile), str(repo_path)],
        check=True,
    )
    return dockerfile


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m repo_probe.builder <repo_path> <image_tag> [python_version]")
        sys.exit(1)

    repo_path = Path(sys.argv[1])
    tag = sys.argv[2]
    py_version = sys.argv[3] if len(sys.argv) > 3 else "3.12"

    if not repo_path.is_dir():
        print(f"Error: {repo_path} is not a directory", file=sys.stderr)
        sys.exit(1)

    setup = detect_test_setup(repo_path)
    print(f"runner:     {setup.runner}")
    print(f"command:    {' '.join(setup.command)}")
    print(f"source:     {setup.source}")
    print(f"confidence: {setup.confidence}")
    print(f"ci_runner:  {setup.ci_runner or '-'}")
    print(f"building image: {tag} (python {py_version})")

    dockerfile = build_image(repo_path, setup, tag, python_version=py_version)
    print(f"dockerfile: {dockerfile}")
    print(f"image:      {tag}")