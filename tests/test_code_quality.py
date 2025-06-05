import subprocess
from pathlib import Path

CHECK_PATHS = [
    str(Path("backend/app")),
    str(Path("scripts")),
    str(Path("tests")),
]


def test_black_conformity():
    cmd = ["black", "--check", *CHECK_PATHS]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_ruff_errors():
    cmd = [
        "ruff",
        "check",
        "--select",
        "F",
        "--ignore",
        "F401,F821",
        *CHECK_PATHS,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
