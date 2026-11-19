import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_custom_model_root_reaches_comfyui_config(tmp_path):
    model_root = tmp_path / "models"
    config_path = tmp_path / "extra_model_paths.yaml"
    env = os.environ.copy()
    env["MODEL_ROOT"] = str(model_root)

    subprocess.run(
        [sys.executable, "-m", "app.model_paths", str(config_path)],
        cwd=ROOT,
        env=env,
        check=True,
    )

    config = json.loads(config_path.read_text(encoding="utf-8"))
    assert config == {
        "autostudio": {
            "base_path": str(model_root),
            "diffusion_models": "diffusion_models",
            "text_encoders": "text_encoders",
            "vae": "vae",
        }
    }
