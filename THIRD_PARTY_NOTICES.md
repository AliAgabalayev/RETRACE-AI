# Third-party notices

## VideoGameQA-Bench demo images

The portable barrel pair derives from [taesiri/VideoGameQA-Bench](https://huggingface.co/datasets/taesiri/VideoGameQA-Bench), dataset revision `2afbfdcc9cb84318845f348c023bb2e92b942e29`, licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Attribution: Mohammad Reza Taesiri, Abhijay Ghildyal, Saman Zadtootaghaj, Nabajeet Barman and Cor-Paul Bezemer, *VideoGameQA-Bench: Evaluating Vision-Language Models for Video Game Quality Assurance* (2025), [paper](https://arxiv.org/abs/2505.15952), [project](https://asgaardlab.github.io/videogameqa-bench/).

Project changes: visual-regression subset selection, internal dev/eval grouping, human frozen labels, conversion to PNG working copies, crops/overlay and QA reports. Authors do not endorse this prototype. Dataset licensing does not transfer all underlying third-party game IP rights. Replay is attributed research/demo evidence; owner should review redistribution requirements for their intended use.

## DINOv2

Meta / facebookresearch, [DINOv2](https://github.com/facebookresearch/dinov2), Oquab et al., *DINOv2: Learning Robust Visual Features without Supervision* (2023). Used frozen `dinov2_vits14`, without training. Code and these weights are Apache-2.0; [pinned source license](https://github.com/facebookresearch/dinov2/blob/7764ea0f912e53c92e82eb78a2a1631e92725fc8/LICENSE), copy in `deploy/DINOV2_LICENSE.txt`. Weights are downloaded during Docker build, not committed. Other DINO variants and their potentially different licenses are not used.

## Active hosted model

Gemini via OpenRouter is a hosted API, not redistributed weights. Owner use is subject to [OpenRouter terms](https://openrouter.ai/terms) and the model provider terms. Credentials and spending controls belong to the owner. Live image uploads leave the application host.

## Historical Qwen baseline

Qwen2.5-VL 3B via Ollama is retained only as the measured historical baseline. It is not in the deployment image and no Qwen weights are distributed. Earlier documentation found a Qwen Research License versus Ollama packaged-license conflict; this task does not resolve or authorize commercial Qwen use. Consult the [Qwen model license](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct/blob/main/LICENSE) before any reuse.

## Runtime packages

Pinned versions are in `requirements.txt`. License identifiers below were checked against installed package metadata on 2026-10-09; dependency distributions retain their own license files. OpenCV deployment uses the headless variant of the same wheel release. Transitive bundled libraries may have additional notices shipped with their packages.

| Package | Version | License |
|---|---|---|
| torch / torchvision | 2.6.0 /0.21.0 | BSD-3-Clause /BSD |
| Streamlit | 1.61.1 | Apache-2.0 |
| opencv-python-headless | 4.12.0.88 | Apache-2.0 (OpenCV), wheel bundled notices |
| NumPy | 2.0.2 | BSD-3-Clause plus bundled notices |
| Pillow | 10.4.0 | HPND |
| pandas | 2.2.2 | BSD-3-Clause |
| PyArrow | 21.0.0 | Apache-2.0 |
| Pydantic | 2.8.2 | MIT |
| PyYAML | 6.0.1 | MIT |
| httpx | 0.27.0 | BSD-3-Clause |
| huggingface_hub | 0.34.4 | Apache-2.0 |
| python-dotenv | 0.21.0 | BSD-3-Clause |

No license for the project's own source is invented here; repository owner must choose any desired redistribution license separately.
