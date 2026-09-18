"""Run a built image as a container and capture the test output."""

import subprocess
import sys
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class TestRun:
    """Result of running the tests for one image."""

    __test__ = False  # tell pytest not to collect this class

    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


def run_image(image_tag: str, timeout_seconds: int = 300) -> TestRun:
    """Run the image as a container, capture output, and return a TestRun.

    Does not raise if tests fail — a non-zero exit code is a valid result.
    Raises subprocess.TimeoutExpired if the container exceeds the timeout.
    """
    start = time.perf_counter()
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", image_tag],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.perf_counter() - start
        return TestRun(
            exit_code=124,  # conventional timeout exit code
            stdout=(exc.stdout or "") if isinstance(exc.stdout, str) else "",
            stderr=f"Container timed out after {timeout_seconds}s",
            duration_seconds=duration,
        )
    duration = time.perf_counter() - start
    return TestRun(
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        duration_seconds=duration,
    )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m repo_probe.runner <image_tag> [timeout_seconds]")
        sys.exit(1)

    tag = sys.argv[1]
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 300

    print(f"running: {tag} (timeout {timeout}s)")
    run = run_image(tag, timeout_seconds=timeout)
    print(f"exit_code: {run.exit_code}")
    print(f"passed:    {run.passed}")
    print(f"duration:  {run.duration_seconds:.2f}s")
    print("--- stdout (tail) ---")
    print("\n".join(run.stdout.splitlines()[-20:]))
    if run.stderr.strip():
        print("--- stderr (tail) ---")
        print("\n".join(run.stderr.splitlines()[-10:]))