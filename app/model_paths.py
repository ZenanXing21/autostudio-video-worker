"""Generate the ComfyUI model search config from the worker's model root."""

import json
import sys
from pathlib import Path

from .config import Settings


def write_extra_model_paths(model_root: Path, destination: Path) -> None:
    paths = {
        "autostudio": {
            "base_path": str(model_root),
            "diffusion_models": "diffusion_models",
            "text_encoders": "text_encoders",
            "vae": "vae",
        }
    }
    # JSON is valid YAML and needs no extra parser dependency to generate.
    destination.write_text(json.dumps(paths, indent=2), encoding="utf-8")


if __name__ == "__main__":
    write_extra_model_paths(Settings().model_root, Path(sys.argv[1]))
