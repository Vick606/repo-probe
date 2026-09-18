<div align="center">

# RepoProbe

**Clone, containerize, and test any Python repo — then emit a structured evaluation report.**

[![CI](https://github.com/Vick606/repo-probe/actions/workflows/ci.yml/badge.svg)](https://github.com/Vick606/repo-probe/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/tests-22%20passed-brightgreen.svg)](#tests)

</div>

---

## What it does

RepoProbe runs a Python repository's test suite inside an isolated Docker container and writes a structured JSON report — reproducibly, from a single command.

```bash
python -m repo_probe https://github.com/pallets/click.git 8.1.7
```

Five stages, one pipeline:

```
clone → detect → build → run → report
```

Given a repo at an exact commit, RepoProbe builds the environment, runs the tests, and records what happened — in a format that downstream tools can parse, diff, and compare.

---

## Why it exists

Evaluating whether code works requires more than running `pytest`. It requires:

- **Reproducibility** — the same commit, the same environment, every time.
- **Isolation** — dependencies for one project must not leak into another.
- **Structured output** — results that downstream tools can parse, diff, and compare.

RepoProbe handles all three, in ~300 lines of tested Python.

---

## Quick start

**Requirements:** Python 3.10+, Docker, Git.

```bash
git clone https://github.com/Vick606/repo-probe.git
cd repo-probe
pip install -e ".[dev]"

python -m repo_probe https://github.com/pallets/click.git 8.1.7
```

**Output:**

```
[1/5] cloning https://github.com/pallets/click.git @ 8.1.7
      commit: 874ca2bc1c30d93a4ac6e36a15ed685eafe89097
[2/5] detecting test setup
      runner=pytest source=setup.cfg confidence=high ci_runner=tox
[3/5] building image repo-probe:8.1.7 (python 3.12)
[4/5] running tests (timeout 300s)
      exit_code=0 passed=True duration=3.40s
[5/5] report written: reports/8.1.7.json
```

**Report** (`reports/8.1.7.json`):

```json
{
  "schema_version": "1.0",
  "repo": {
    "url": "https://github.com/pallets/click.git",
    "ref": "8.1.7",
    "commit": "874ca2bc1c30d93a4ac6e36a15ed685eafe89097"
  },
  "setup": {
    "runner": "pytest",
    "command": ["pytest", "-v"],
    "source": "setup.cfg",
    "confidence": "high",
    "ci_runner": "tox"
  },
  "result": {
    "exit_code": 0,
    "passed": true,
    "duration_seconds": 3.4,
    "stdout_tail": "589 passed, 21 skipped, 1 xfailed in 1.91s"
  }
}
```

---

## CLI options

| Flag | Default | Description |
|---|---|---|
| `repo_url` | *required* | Git repository URL |
| `ref` | *required* | Branch, tag, or commit SHA |
| `--tag` | `repo-probe:<ref>` | Docker image tag |
| `--python` | `3.12` | Python version in the container |
| `--report` | `reports/<ref>.json` | Report output path |
| `--timeout` | `300` | Container timeout (seconds) |
| `--keep-image` | `false` | Keep the Docker image after the run |

---

## Architecture

```
repo_probe/
├── __main__.py     # CLI orchestrator — wires the five stages together
├── cloner.py       # Clone a repo and check out a specific ref
├── detector.py     # Detect the test runner (pytest / tox / nox / unittest)
├── builder.py      # Generate a Dockerfile and build the image
├── runner.py       # Run the container, capture output and duration
└── reporter.py     # Write the structured JSON report
```

Each module is independently testable. The CLI only orchestrates.

---

## Detection strategy

RepoProbe infers the test runner using a priority order:

| Priority | Signal | Confidence |
|---|---|---|
| 1 | pytest config in `pytest.ini` / `pyproject.toml` / `setup.cfg` | high |
| 2 | Runner named in a CI workflow (`.github/workflows/*.yml`) | high |
| 3 | `tox.ini` present | high |
| 4 | `noxfile.py` present | high |
| 5 | Fallback to `pytest -v` | low |

**Design decision:** when a repo's CI uses `tox` but pytest config exists, RepoProbe runs `pytest` directly and records `ci_runner: tox` in the report. Running `tox` inside a slim container is fragile and slow; the goal is to run tests reliably, not to reproduce CI exactly.

---

## Tests

```bash
pytest -v
```

**22 tests, all passing**, covering every module:

```
tests/test_cloner.py     2 tests
tests/test_detector.py   5 tests
tests/test_builder.py    4 tests
tests/test_runner.py     3 tests
tests/test_reporter.py   5 tests
tests/test_cli.py        3 tests
```

---

## Known limitations

> Honest limitations matter more than polished claims.

- **Python only.** No Node, Go, Rust, or JVM support.
- **No patch evaluation yet.** v0.1 runs tests; it does not apply or score a candidate fix.
- **No test-count parsing.** Reports include the raw output tail, not extracted `passed=N failed=M`.
- **Limited system dependencies.** Repos requiring `libxml2`, `gcc`, or similar will fail to build.
- **Whole-suite runs only.** No filtering to a specific test file or function.
- **Single container.** No parallel or batch execution.

These are deliberate. v0.1 proves the core pipeline; each item above is scoped for a later release.

---

## Roadmap

- [x] **v0.1** — Core pipeline (clone → detect → build → run → report)
- [ ] **v0.2** — Parse pytest output into structured test counts
- [ ] **v0.3** — Apply candidate patch; compute FAIL_TO_PASS / PASS_TO_PASS
- [ ] **v0.4** — Batch runs across multiple repos
- [ ] **v0.5** — Integrate an LLM to generate and evaluate patches

---

## License

[MIT](LICENSE)

---

<div align="center">

*Reproducible test execution for Python repositories — built for engineers who need to know whether the code actually works.*

</div>