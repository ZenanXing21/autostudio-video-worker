import subprocess

import pytest

from app.comfyui_manager import ComfyError, ComfyUI
from app.config import Settings


def test_failed_comfyui_start_keeps_stderr_in_workspace_log(monkeypatch, tmp_path):
    log_path = tmp_path / "logs" / "comfyui.log"
    comfy = ComfyUI(Settings(comfy_log_path=log_path))
    monkeypatch.setattr(comfy, "ready", lambda: False)

    class FinishedProcess:
        returncode = 17

        def poll(self):
            return self.returncode

    def fake_popen(command, stdout, stderr):
        assert command == ["bash", "/app/scripts/start_comfyui.sh"]
        assert stderr == subprocess.STDOUT
        stdout.write("ModuleNotFoundError: missing_package\n")
        stdout.flush()
        return FinishedProcess()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    with pytest.raises(ComfyError, match="ComfyUI exited with code 17"):
        comfy.start()

    assert "ModuleNotFoundError: missing_package" in log_path.read_text(encoding="utf-8")
