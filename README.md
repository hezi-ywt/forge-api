# ForgeAPI

Standalone Python client for Stable Diffusion WebUI Forge.

## Install

```powershell
python -m pip install -e .
```

This installs both the `forge_api` package and the `forge-preflight` CLI into
the project's `.venv`; it does not modify the global Python environment or
global Codex Skill directory.

Consumer projects should install ForgeAPI into their own virtual environment
with `python -m pip install -e <path-to-ForgeAPI>` during development. The
environment in this repository is only for ForgeAPI development and tests.

To install the package into the project-local environment in one step:

```powershell
python scripts/install.py
```

## Read-only preflight

```powershell
python scripts/forge_preflight.py --url 127.0.0.1:7860
```

## Python API

```python
from forge_api import ADetailerConfig, ForgeClient

client = ForgeClient("127.0.0.1:7860")
result = client.txt2img(
    prompt="...",
    negative_prompt="...",
    adetailer=ADetailerConfig.face_repair(prompt="..."),
    seed=42,
)
result.save("out/image.png")
```

The client uses Forge's REST API and Python's standard library. It supports
read-only service inspection, txt2img, img2img, Hires fix, IPA/ControlNet,
ADetailer, presets implementing `forge_payload()`, and reproducible sidecar
metadata.

The bundled Skill is at `skills/forge-api/SKILL.md`; its references and
Skill-specific scripts are colocated under that directory.
