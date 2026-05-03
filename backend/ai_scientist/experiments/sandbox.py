"""Subprocess-based execution of LLM-generated Python code.

Security note: this is a *development* sandbox. It enforces a wall-clock timeout,
output size cap, and writes inside a dedicated workspace directory, but it does NOT
provide containerised isolation. For untrusted code in production, run inside Docker
or a gVisor/firecracker microVM instead.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from ..config import get_settings


@dataclass
class SandboxResult:
    returncode: int | None
    stdout: str
    stderr: str
    duration_s: float
    timed_out: bool
    workdir: Path
    artifacts: list[Path] = field(default_factory=list)


async def run_python_in_sandbox(
    code: str,
    *,
    requirements: list[str] | None = None,
    timeout_s: int | None = None,
    max_output_bytes: int | None = None,
    workdir: Path | None = None,
    cleanup: bool = False,
) -> SandboxResult:
    settings = get_settings()
    timeout_s = timeout_s or settings.sandbox_timeout_s
    cap = max_output_bytes or settings.sandbox_max_output_bytes
    base = Path(workdir) if workdir else settings.workspace / f"run_{uuid4().hex[:10]}"
    base.mkdir(parents=True, exist_ok=True)
    base = base.resolve()  # ensure absolute so subprocess cwd + script paths are unambiguous

    script = base / "experiment.py"
    script.write_text(code, encoding="utf-8")

    if requirements:
        (base / "requirements.txt").write_text("\n".join(requirements), encoding="utf-8")
        await _run([sys.executable, "-m", "pip", "install", "-q", *requirements], base, timeout_s)

    started = time.time()
    timed_out = False
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "-u",
            script.name,  # cwd is `base`; pass just the filename to avoid path-resolution issues on Windows
            cwd=str(base),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
            rc = proc.returncode
        except asyncio.TimeoutError:
            timed_out = True
            proc.kill()
            try:
                stdout_b, stderr_b = await proc.communicate()
            except Exception:
                stdout_b, stderr_b = b"", b""
            rc = None
    except Exception as e:
        return SandboxResult(
            returncode=-1,
            stdout="",
            stderr=f"Sandbox failed to start: {e!r}",
            duration_s=time.time() - started,
            timed_out=False,
            workdir=base,
        )

    duration = time.time() - started
    stdout = _truncate(stdout_b.decode("utf-8", errors="replace"), cap)
    stderr = _truncate(stderr_b.decode("utf-8", errors="replace"), cap)

    artifacts = sorted(
        p for p in base.glob("**/*") if p.is_file() and p.name not in {"experiment.py", "requirements.txt"}
    )

    result = SandboxResult(
        returncode=rc,
        stdout=stdout,
        stderr=stderr,
        duration_s=duration,
        timed_out=timed_out,
        workdir=base,
        artifacts=artifacts,
    )
    if cleanup:
        shutil.rmtree(base, ignore_errors=True)
    return result


async def _run(cmd: list[str], cwd: Path, timeout_s: int) -> None:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(Path(cwd).resolve()),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
    except asyncio.TimeoutError:
        proc.kill()


def _truncate(s: str, cap: int) -> str:
    if len(s.encode("utf-8")) <= cap:
        return s
    return s[: cap // 2] + f"\n... [truncated {len(s) - cap // 2} chars] ...\n"
