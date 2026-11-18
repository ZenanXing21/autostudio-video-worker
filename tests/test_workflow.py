import json
from pathlib import Path

import pytest

from app.validators import InputError, parse_request
from app.workflow_engine import build_prompt, validate_graph


ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize("mode", ["t2v", "i2v"])
def test_graphs_are_separate_and_connected(mode):
    ui = json.loads((ROOT / "workflows" / f"wan22_{mode}.json").read_text())
    api = json.loads((ROOT / "workflows" / f"wan22_{mode}.api.json").read_text())
    assert ui["version"] == 0.4
    assert {str(n["id"]) for n in ui["nodes"]} == set(api)
    assert ("56" in api) == (mode == "i2v")
    validate_graph(api, {node["class_type"] for node in api.values()})
    for link_id, source, slot, target, index, typ in ui["links"]:
        nodes = {n["id"]: n for n in ui["nodes"]}
        assert nodes[source]["outputs"][slot]["type"] == typ
        assert nodes[target]["inputs"][index]["link"] == link_id


def test_dynamic_values_and_frame_count():
    request = parse_request({"task_type": "video_generation", "mode": "t2v", "prompt": "hello",
                             "negative_prompt": "blur", "duration": 3, "resolution": "480p", "fps": 24, "seed": 17})
    graph = build_prompt(request, None, "job_1")
    assert graph["55"]["inputs"]["length"] == 73
    assert graph["55"]["inputs"]["width"] == 832
    assert graph["3"]["inputs"]["seed"] == 17
    assert graph["6"]["inputs"]["text"] == "hello"
    assert graph["7"]["inputs"]["text"] == "blur"
    assert graph["58"]["inputs"]["filename_prefix"] == "autostudio/job_1"


def test_i2v_image_replacement():
    request = parse_request({"task_type": "video_generation", "mode": "i2v", "prompt": "hello",
                             "image_file": "aGVsbG8="})
    graph = build_prompt(request, "uploaded.png", "job_2")
    assert graph["56"]["inputs"]["image"] == "uploaded.png"
    assert graph["55"]["inputs"]["start_image"] == ["56", 0]


@pytest.mark.parametrize("override", [{"fps": 30}, {"duration": 6}, {"resolution": "1080p"}])
def test_unsupported_profile_rejected(override):
    data = {"task_type": "video_generation", "mode": "t2v", "prompt": "hello", **override}
    with pytest.raises(InputError):
        parse_request(data)
