"""Build-time cache of the exact DINO source/weights verified against C2. No VLM/key use."""
import hashlib
import os
from pathlib import Path
import urllib.request
import zipfile
import tempfile

SOURCE_SHA = "7764ea0f912e53c92e82eb78a2a1631e92725fc8"
WEIGHTS_SHA256 = "b938bf1bc15cd2ec0feacfe3a1bb553fe8ea9ca46a7e1d8d00217f29aef60cd9"


def main():
    hub = Path(os.environ["TORCH_HOME"]) / "hub"
    target = hub / "facebookresearch_dinov2_main"
    if target.exists():
        raise RuntimeError("Use an empty deployment cache; existing user cache will not be overwritten")
    hub.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / "source.zip"
        urllib.request.urlretrieve(f"https://codeload.github.com/facebookresearch/dinov2/zip/{SOURCE_SHA}", archive)
        with zipfile.ZipFile(archive) as z:
            prefix = f"dinov2-{SOURCE_SHA}/"
            for name in z.namelist():
                if not name.startswith(prefix) or name.endswith("/"):
                    continue
                relative = Path(name[len(prefix):])
                if relative.is_absolute() or ".." in relative.parts:
                    raise RuntimeError("Unsafe source archive path")
                dest = target / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(z.read(name))
    weights = hub / "checkpoints/dinov2_vits14_pretrain.pth"
    weights.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve("https://dl.fbaipublicfiles.com/dinov2/dinov2_vits14/dinov2_vits14_pretrain.pth", weights)
    if hashlib.sha256(weights.read_bytes()).hexdigest() != WEIGHTS_SHA256:
        raise RuntimeError("DINO checkpoint checksum mismatch")
    (target / "DEPLOYMENT_SOURCE_SHA").write_text(SOURCE_SHA)
    print("Verified DINO source and checkpoint cached; no inference")


if __name__ == "__main__":
    main()
