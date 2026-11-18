import base64
import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse


class InputError(ValueError):
    pass


@dataclass(frozen=True)
class VideoRequest:
    mode: str
    prompt: str
    negative_prompt: str
    duration: int
    resolution: str
    fps: int
    seed: int
    width: int
    height: int
    frames: int
    image_url: str | None
    image_bytes: bytes | None


def public_https_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise InputError("image_url must be a public HTTPS URL")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror as exc:
        raise InputError("image_url DNS lookup failed") from exc
    if not addresses or any(not ipaddress.ip_address(info[4][0]).is_global for info in addresses):
        raise InputError("image_url resolves to a non-public address")
    return url


def parse_request(raw: dict) -> VideoRequest:
    if not isinstance(raw, dict) or raw.get("task_type") != "video_generation":
        raise InputError("task_type must be video_generation")
    mode = raw.get("mode")
    if mode not in ("t2v", "i2v"):
        raise InputError("mode must be t2v or i2v")
    prompt = raw.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 4000:
        raise InputError("prompt must contain 1-4000 characters")
    negative = raw.get("negative_prompt", "")
    if not isinstance(negative, str) or len(negative) > 4000:
        raise InputError("negative_prompt must be a string of at most 4000 characters")
    duration = raw.get("duration", 5)
    fps = raw.get("fps", 24)
    seed = raw.get("seed", 0)
    resolution = raw.get("resolution", "720p")
    if type(duration) is not int or not 1 <= duration <= 5:
        raise InputError("24GB profile supports integer duration 1-5 seconds")
    if fps != 24:
        raise InputError("Wan 2.2 TI2V-5B profile supports fps=24; no frame interpolation is installed")
    if type(seed) is not int or not 0 <= seed < 2**64:
        raise InputError("seed must be an unsigned 64-bit integer")
    sizes = {"720p": (1280, 704), "720p_portrait": (704, 1280), "480p": (832, 480)}
    if resolution not in sizes:
        raise InputError("resolution must be 720p, 720p_portrait or 480p")
    image_url = raw.get("image_url")
    image_file = raw.get("image_file")
    if mode == "i2v" and bool(image_url) == bool(image_file):
        raise InputError("i2v requires exactly one of image_url or base64 image_file")
    if mode == "t2v" and (image_url or image_file):
        raise InputError("t2v must not contain an image")
    if image_url is not None:
        if not isinstance(image_url, str):
            raise InputError("image_url must be a string")
        image_url = public_https_url(image_url)
    image_bytes = None
    if image_file is not None:
        if not isinstance(image_file, str):
            raise InputError("image_file must be base64 encoded image data")
        encoded = image_file.split(",", 1)[-1] if image_file.startswith("data:image/") else image_file
        if len(encoded) > 28_000_000:
            raise InputError("image_file is too large")
        try:
            image_bytes = base64.b64decode(encoded, validate=True)
        except (ValueError, base64.binascii.Error) as exc:
            raise InputError("image_file is invalid base64") from exc
    width, height = sizes[resolution]
    return VideoRequest(mode, prompt.strip(), negative, duration, resolution, fps, seed,
                        width, height, duration * fps + 1, image_url, image_bytes)
