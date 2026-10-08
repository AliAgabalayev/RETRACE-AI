# Third-party notices

Verified 2026-10-09 unless marked otherwise.

## Dataset: VideoGameQA-Bench
- Source: https://huggingface.co/datasets/taesiri/VideoGameQA-Bench (revision `2afbfdcc9cb84318845f348c023bb2e92b942e29`); project page https://asgaardlab.github.io/videogameqa-bench/
- License: CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Used here: the visual-regression subset, selected image pairs only, resized/converted to PNG working copies. Original files are kept unmodified under `data/raw/`.
- Attribution: please cite the paper:
  Taesiri, Mohammad Reza; Ghildyal, Abhijay; Zadtootaghaj, Saman; Barman, Nabajeet; Bezemer, Cor-Paul. "VideoGameQA-Bench: Evaluating Vision-Language Models for Video Game Quality Assurance." arXiv:2505.15952 (2025). https://arxiv.org/abs/2505.15952
  (Authors and title read from the arXiv abstract page metadata.)
- Changes made by this project: subset selection, relabelling of `ground_truth` into `bug`/`no_bug`, internal dev/eval split. No endorsement by the authors is implied.

## Model: DINOv2
- facebookresearch/dinov2, https://github.com/facebookresearch/dinov2. Repository code license: Apache License 2.0 (LICENSE file in the repository `main` branch verified). Used as frozen `dinov2_vits14`, inference only.
- Pretrained weights are obtained through `torch.hub`. The main README (line 660, "License" section) states: "DINOv2 code and model weights are released under the Apache License 2.0". Note the same README also lists separate non-commercial licenses for other variants in the repo (X-Ray-DINO, Cell-DINO); those are not used here. Weights are not redistributed by this project.
- Reference: Oquab et al., "DINOv2: Learning Robust Visual Features without Supervision", 2023 (arXiv:2304.07193).

## Model: Qwen2.5-VL 3B via Ollama
- Ollama tag `qwen2.5vl:3b` (3.2 GB), run locally; no data leaves the machine.
- **License conflict to resolve, do not assume:** the Hugging Face repository `Qwen/Qwen2.5-VL-3B-Instruct` ships `LICENSE` = **Qwen RESEARCH LICENSE AGREEMENT** (README `license_name: qwen-research`), which grants rights "for non-commercial purposes only" (non-commercial = research or evaluation) and requires a separate license from Alibaba Cloud for commercial use. The Ollama package for this tag, however, bundles a plain **Apache License 2.0** text (`ollama show qwen2.5vl:3b --license`). The two disagree. Treat the stricter Qwen Research License as binding until verified: this hackathon prototype is research/evaluation use only; do not use for commercial purposes without checking.
- Authors: Qwen Team, Alibaba Cloud. Reference: Bai et al., "Qwen2.5-VL Technical Report", arXiv:2502.13923 (citation from memory of the report; verify before publishing).
- Ollama itself: https://ollama.com (MIT-licensed open source server; not re-verified here).

## Python libraries (installed in `.venv`, versions from `pip list`)
Used unmodified and not redistributed; each under its own license, to be confirmed from package metadata before any redistribution.
- PyTorch 2.12.0 and torchvision 0.27.0 (BSD-style licenses)
- Streamlit 1.65.0 (Apache-2.0)
- OpenCV (opencv-python 4.13.0.92; Apache-2.0 for recent OpenCV)
- NumPy 2.3.5 (BSD-3-Clause), Pillow 12.3.0 (HPND), pandas 2.3.3 (BSD-3-Clause), PyArrow 24.0.0 (Apache-2.0)
- Pydantic 2.12.5 (MIT), PyYAML 6.0.3 (MIT), httpx 0.28.1 (BSD-3-Clause), huggingface_hub 1.8.0 (Apache-2.0), pytest 9.1.1 (MIT)
License names in this section are from general knowledge of those projects, not re-fetched; marked unverified.
