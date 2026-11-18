import copy
import json
from pathlib import Path

from .validators import VideoRequest


ROOT = Path(__file__).resolve().parent.parent


def build_prompt(request: VideoRequest, image_name: str | None, task_id: str) -> dict:
    path = ROOT / "workflows" / f"wan22_{request.mode}.api.json"
    graph = copy.deepcopy(json.loads(path.read_text(encoding="utf-8")))
    graph["6"]["inputs"]["text"] = request.prompt
    graph["7"]["inputs"]["text"] = request.negative_prompt
    graph["3"]["inputs"]["seed"] = request.seed
    graph["55"]["inputs"].update(width=request.width, height=request.height, length=request.frames)
    graph["57"]["inputs"]["fps"] = request.fps
    graph["58"]["inputs"]["filename_prefix"] = f"autostudio/{task_id}"
    if request.mode == "i2v":
        if not image_name:
            raise ValueError("i2v image was not uploaded")
        graph["56"]["inputs"]["image"] = image_name
    return graph


def validate_graph(graph: dict, available_nodes: set[str]) -> None:
    missing = {node["class_type"] for node in graph.values()} - available_nodes
    if missing:
        raise RuntimeError(f"ComfyUI is missing nodes: {sorted(missing)}")
    for node_id, node in graph.items():
        for value in node["inputs"].values():
            if isinstance(value, list) and len(value) == 2 and isinstance(value[0], str):
                if value[0] not in graph or not isinstance(value[1], int):
                    raise RuntimeError(f"Invalid connection on node {node_id}")
