import pytest

from ai_scientist.experiments.sandbox import run_python_in_sandbox


@pytest.mark.asyncio
async def test_sandbox_runs_simple_code(tmp_path):
    code = "print('hello from sandbox')\n"
    res = await run_python_in_sandbox(code, workdir=tmp_path, timeout_s=15)
    assert res.returncode == 0
    assert "hello from sandbox" in res.stdout
    assert res.timed_out is False


@pytest.mark.asyncio
async def test_sandbox_times_out(tmp_path):
    code = "import time\nfor _ in range(100):\n    time.sleep(1)\n"
    res = await run_python_in_sandbox(code, workdir=tmp_path, timeout_s=2)
    assert res.timed_out is True


@pytest.mark.asyncio
async def test_sandbox_captures_stderr(tmp_path):
    code = "import sys\nsys.stderr.write('boom\\n')\nraise SystemExit(3)\n"
    res = await run_python_in_sandbox(code, workdir=tmp_path, timeout_s=10)
    assert res.returncode == 3
    assert "boom" in res.stderr
