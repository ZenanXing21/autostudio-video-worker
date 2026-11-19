import subprocess

import pytest

from app.gpu_manager import GPUError, check_gpu


def test_mig_memory_permission_error_does_not_block_startup(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(
        args[0], 0, "NVIDIA B300 SXM6 AC, [Insufficient Permissions]\n", ""
    ))

    assert check_gpu() == {"name": "NVIDIA B300 SXM6 AC", "memory_mib": None}


def test_known_gpu_memory_still_enforces_minimum(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(
        args[0], 0, "NVIDIA RTX 3090, 24576\n", ""
    ))
    assert check_gpu()["memory_mib"] == 24576

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(
        args[0], 0, "NVIDIA RTX 3060, 12288\n", ""
    ))
    with pytest.raises(GPUError, match="22,000 MiB"):
        check_gpu()
