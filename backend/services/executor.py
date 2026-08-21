import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from backend.config import ROOT_DIR, settings
from backend.schemas.scenario import RunResult


def run_python_code(code: str, scenario_id: str, timeout: int | None = None) -> RunResult:
    """Run Python code in an isolated subprocess and capture its output."""
    timeout = timeout or settings.run_timeout_seconds
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT_DIR) + os.pathsep + env.get("PYTHONPATH", "")
        # Force UTF-8 output in the child so scenario scripts can print
        # non-ASCII symbols even on Windows consoles that default to a
        # non-UTF-8 code page (e.g. cp1256).
        env["PYTHONIOENCODING"] = "utf-8"

        started = time.perf_counter()
        try:
            proc = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                cwd=ROOT_DIR,
                env=env,
            )
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            if not stderr:
                stderr = f"Execution timed out after {timeout} seconds."
            return RunResult(
                scenario_id=scenario_id,
                stdout=stdout,
                stderr=stderr,
                exit_code=-1,
                duration_ms=int((time.perf_counter() - started) * 1000),
                timed_out=timed_out,
            )
        duration_ms = int((time.perf_counter() - started) * 1000)

        return RunResult(
            scenario_id=scenario_id,
            stdout=proc.stdout,
            stderr=proc.stderr,
            exit_code=proc.returncode,
            duration_ms=duration_ms,
            timed_out=False,
        )
    finally:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
