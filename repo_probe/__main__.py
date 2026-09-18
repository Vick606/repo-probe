"""RepoProbe CLI: clone, detect, build, run, and report on a Python repo."""

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from repo_probe.builder import build_image
from repo_probe.cloner import clone_repo
from repo_probe.detector import detect_test_setup
from repo_probe.reporter import build_report, write_report
from repo_probe.runner import run_image


def _safe_tag(ref: str) -> str:
    """Turn a ref into something usable as a Docker tag."""
    return ref.replace("/", "-").replace(":", "-")


def _head_commit(repo_path: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="repo-probe",
        description="Run a Python repo's test suite in Docker and write a JSON report.",
    )
    parser.add_argument("repo_url", help="Git URL of the repository")
    parser.add_argument("ref", help="Branch, tag, or commit SHA to check out")
    parser.add_argument("--tag", default=None, help="Docker image tag (default: repo-probe:<ref>)")
    parser.add_argument("--python", default="3.12", help="Python version for the image")
    parser.add_argument("--report", default=None, help="Path to write the JSON report")
    parser.add_argument("--timeout", type=int, default=300, help="Container timeout in seconds")
    parser.add_argument(
        "--keep-image",
        action="store_true",
        help="Do not delete the built image after the run",
    )

    args = parser.parse_args(argv)

    safe = _safe_tag(args.ref)
    image_tag = args.tag or f"repo-probe:{safe}"
    report_path = Path(args.report) if args.report else Path("reports") / f"{safe}.json"

    with tempfile.TemporaryDirectory() as tmp:
        repo_path = Path(tmp) / "repo"

        _log(f"[1/5] cloning {args.repo_url} @ {args.ref}")
        clone_repo(args.repo_url, args.ref, repo_path)
        commit = _head_commit(repo_path)
        _log(f"      commit: {commit}")

        _log("[2/5] detecting test setup")
        setup = detect_test_setup(repo_path)
        _log(
            f"      runner={setup.runner} source={setup.source} "
            f"confidence={setup.confidence} ci_runner={setup.ci_runner or '-'}"
        )

        _log(f"[3/5] building image {image_tag} (python {args.python})")
        build_image(repo_path, setup, image_tag, python_version=args.python)

        _log(f"[4/5] running tests (timeout {args.timeout}s)")
        run = run_image(image_tag, timeout_seconds=args.timeout)
        _log(f"      exit_code={run.exit_code} passed={run.passed} duration={run.duration_seconds:.2f}s")

        report = build_report(
            repo_url=args.repo_url,
            ref=args.ref,
            commit=commit,
            setup=setup,
            run=run,
        )
        written = write_report(report, report_path)
        _log(f"[5/5] report written: {written}")

        if not args.keep_image:
            _log(f"      removing image {image_tag}")
            subprocess.run(
                ["docker", "rmi", image_tag],
                check=False,
                capture_output=True,
            )

    print(str(written))
    return 0 if run.passed else 1


if __name__ == "__main__":
    sys.exit(main())