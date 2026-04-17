import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from pytest import mark


_CONFIG = """
- rule: "0 0 1 1 *"
  listener:
    type: rss
    params:
      url: http://127.0.0.1:1/feed
  transport:
    type: telegram_bot
    params:
      token: fake-token
      to: "@chan"
"""


def _spawn(config: Path) -> subprocess.Popen[str]:
    return subprocess.Popen(  # noqa: S603
        [
            sys.executable,
            "-m",
            "feedforbot",
            "-v",
            "--cache-dsn",
            "memory:",
            str(config),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )


def _wait_for(
    proc: subprocess.Popen[str],
    needle: str,
    timeout: float,
) -> str:
    deadline = time.monotonic() + timeout
    buf: list[str] = []
    assert proc.stdout is not None
    os.set_blocking(proc.stdout.fileno(), False)
    while time.monotonic() < deadline:
        try:
            chunk = proc.stdout.read()
        except BlockingIOError:
            chunk = None
        if chunk:
            buf.append(chunk)
            if needle in "".join(buf):
                return "".join(buf)
        time.sleep(0.05)
    return "".join(buf)


def _drain(proc: subprocess.Popen[str]) -> str:
    if proc.stdout is None:
        return ""
    try:
        remainder = proc.stdout.read()
    except (BlockingIOError, ValueError):
        remainder = None
    return remainder or ""


@mark.skipif(
    sys.platform == "win32",
    reason="POSIX signal handling only",
)
def test_sigterm_triggers_graceful_shutdown(tmp_path: Path) -> None:
    config = tmp_path / "config.yml"
    config.write_text(_CONFIG)

    proc = _spawn(config)
    try:
        start_out = _wait_for(proc, "scheduler_start", timeout=15.0)
        assert "scheduler_start" in start_out, start_out

        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=10.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise

        assert proc.returncode == 0, (start_out, proc.returncode)
        combined = start_out + _drain(proc)
        assert "shutdown_start" in combined, combined
        assert "shutdown_complete" in combined, combined
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5.0)


@mark.skipif(
    sys.platform == "win32",
    reason="POSIX signal handling only",
)
def test_double_sigint_forces_shutdown(tmp_path: Path) -> None:
    config = tmp_path / "config.yml"
    config.write_text(_CONFIG)

    proc = _spawn(config)
    try:
        start_out = _wait_for(proc, "scheduler_start", timeout=15.0)
        assert "scheduler_start" in start_out, start_out

        proc.send_signal(signal.SIGINT)
        time.sleep(0.1)
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=10.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise

        combined = start_out + _drain(proc)
        assert "shutdown_start" in combined, combined
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5.0)
