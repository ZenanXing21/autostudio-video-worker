"""Build two importable ComfyUI UI graphs and their API equivalents from verified core nodes."""
import json
from pathlib import Path


OUT = Path(__file__).resolve().parent.parent / "workflows"


def build(mode: str) -> tuple[dict, dict]:
    spec = [
        (37, "UNETLoader", {"unet_name": "wan2.2_ti2v_5B_fp16.safetensors", "weight_dtype": "default"}, ["MODEL"]),
        (38, "CLIPLoader", {"clip_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors", "type": "wan", "device": "default"}, ["CLIP"]),
        (39, "VAELoader", {"vae_name": "wan2.2_vae.safetensors"}, ["VAE"]),
        (48, "ModelSamplingSD3", {"model": ["37", 0], "shift": 8}, ["MODEL"]),
        (6, "CLIPTextEncode", {"clip": ["38", 0], "text": "A futuristic AI laboratory"}, ["CONDITIONING"]),
        (7, "CLIPTextEncode", {"clip": ["38", 0], "text": ""}, ["CONDITIONING"]),
        (55, "Wan22ImageToVideoLatent", {"vae": ["39", 0], "width": 1280, "height": 704, "length": 121, "batch_size": 1}, ["LATENT"]),
        (3, "KSampler", {"model": ["48", 0], "positive": ["6", 0], "negative": ["7", 0],
                         "latent_image": ["55", 0], "seed": 12345, "steps": 20, "cfg": 5,
                         "sampler_name": "uni_pc", "scheduler": "simple", "denoise": 1}, ["LATENT"]),
        (8, "VAEDecode", {"samples": ["3", 0], "vae": ["39", 0]}, ["IMAGE"]),
        (57, "CreateVideo", {"images": ["8", 0], "fps": 24}, ["VIDEO"]),
        (58, "SaveVideo", {"video": ["57", 0], "filename_prefix": "autostudio/example",
                            "format": "mp4"}, ["VIDEO"]),
    ]
    if mode == "i2v":
        spec.insert(6, (56, "LoadImage", {"image": "example.png"}, ["IMAGE", "MASK"]))
        spec[7][2]["start_image"] = ["56", 0]
    api = {str(i): {"class_type": typ, "inputs": inputs} for i, typ, inputs, _ in spec}
    links = []
    nodes = []
    for order, (i, typ, inputs, outputs) in enumerate(spec):
        node = {"id": i, "type": typ, "pos": [100 + order % 4 * 350, 100 + order // 4 * 300],
                "size": [300, 180], "flags": {}, "order": order, "mode": 0,
                "inputs": [], "outputs": [{"name": name, "type": name, "links": []} for name in outputs],
                "properties": {"Node name for S&R": typ, "cnr_id": "comfy-core"}, "widgets_values": []}
        nodes.append(node)
    by_id = {str(n["id"]): n for n in nodes}
    # UI widgets follow the official template's ordering.
    widgets = {
        "UNETLoader": ["unet_name", "weight_dtype"], "CLIPLoader": ["clip_name", "type", "device"],
        "VAELoader": ["vae_name"], "ModelSamplingSD3": ["shift"], "CLIPTextEncode": ["text"],
        "Wan22ImageToVideoLatent": ["width", "height", "length", "batch_size"],
        "KSampler": ["seed", "steps", "cfg", "sampler_name", "scheduler", "denoise"],
        "CreateVideo": ["fps"], "SaveVideo": ["filename_prefix", "format"],
        "LoadImage": ["image", "image"],
    }
    for i, typ, inputs, _ in spec:
        node = by_id[str(i)]
        node["widgets_values"] = [inputs.get(k, "image") for k in widgets.get(typ, [])]
        if typ == "KSampler":
            node["widgets_values"].insert(1, "fixed")
        if typ == "SaveVideo":
            node["widgets_values"].append("auto")
        for key, value in inputs.items():
            if isinstance(value, list) and len(value) == 2 and isinstance(value[0], str) and value[0].isdigit():
                source, slot = value
                source_node = by_id[source]
                output_type = source_node["outputs"][slot]["type"]
                link_id = len(links) + 1
                links.append([link_id, int(source), slot, i, len(node["inputs"]), output_type])
                source_node["outputs"][slot]["links"].append(link_id)
                node["inputs"].append({"name": key, "type": output_type, "link": link_id})
    for node in nodes:
        for output in node["outputs"]:
            if not output["links"]:
                output["links"] = None
    ui = {"id": f"autostudio-wan22-{mode}", "revision": 0,
          "last_node_id": max(n["id"] for n in nodes), "last_link_id": len(links),
          "nodes": nodes, "links": links, "groups": [], "config": {}, "extra": {}, "version": 0.4}
    return ui, api


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for mode in ("t2v", "i2v"):
        ui, api = build(mode)
        (OUT / f"wan22_{mode}.json").write_text(json.dumps(ui, indent=2) + "\n", encoding="utf-8")
        (OUT / f"wan22_{mode}.api.json").write_text(json.dumps(api, indent=2) + "\n", encoding="utf-8")
