---
name: forge-api
description: Use a local or remote Stable Diffusion WebUI Forge service through a small Python API package for health checks, txt2img, Hires fix, IPA/ControlNet, ADetailer, and saved generation results. Use when an agent needs to connect to Forge by URL or port and run or inspect image generation; do not use for ComfyUI workflows.
metadata:
  requires:
    bins: ["forge-preflight"]
---

# Forge API

This Skill is the routing and usage guide for the standalone ForgeAPI project
containing this file. The package is independent of the AutoMuse application
package. Do not copy Forge client code into `automuse/` or this Skill.

## Connection

Ask for or derive the Forge base URL. A port alone means
`http://127.0.0.1:<port>`; do not guess a remote host. `ForgeClient` also
accepts `AUTOMUSE_FORGE_URL` and defaults to `http://127.0.0.1:7860`.

Run the read-only preflight before a real generation:

```powershell
python skills/forge-api/scripts/forge_preflight.py --url http://127.0.0.1:7860
```

Preflight checks `/sdapi/v1/progress`, reports the current checkpoint when
available, and lists the basic Forge REST endpoints. It does not submit a
generation.

## Use the package

Consumer projects install ForgeAPI into their own project environment. The
`.venv` created by this repository is only for developing and testing
ForgeAPI; a pipeline must not depend on that environment or on global Python.
From the consumer project's root, install the package with an editable path
during development or a pinned release when the API is being consumed as a
stable dependency:

```powershell
python -m pip install -e <path-to-ForgeAPI>
```

Install the standalone package into the project-local environment with the
repository installer:

```powershell
python scripts/install.py
```

Or install only the Python package with `python -m pip install -e .` inside an
already activated project environment,
then import it. A preset only needs to implement
`forge_payload() -> dict`; AutoMuse presets already satisfy this protocol.

For a longer-lived local environment, install the package in editable mode:

```powershell
python -m pip install -e .
```

```python
from forge_api import ForgeClient, ADetailerConfig, IPAUnit

client = ForgeClient("http://127.0.0.1:7860")
result = client.txt2img(
    prompt="...",
    negative_prompt="...",
    width=896,
    height=1216,
    steps=28,
    cfg_scale=6.5,
    sampler_name="Euler a",
    scheduler="exponential",
    adetailer=ADetailerConfig.face_repair(prompt="..."),
    seed=42,
)
result.save("out/forge/image.png")
```

Use `IPAUnit.from_reference(...)` for an image reference. Use
`hr_additional_modules=[]` or the client's Hires arguments explicitly; Forge
can fail when this field is sent as JSON `null`.

## Modes

- **Inspect:** run preflight or call `progress()`, `options()`, `samplers()`,
  `loras()`, `checkpoints()`, and `vaes()`. These are read-only.
- **Generate:** call `txt2img()` or `img2img()` only after the user has asked
  for an image generation.
- **Recover:** inspect progress and errors. Interrupting or clearing Forge is
  intentionally outside this package until explicitly requested.

## Operational boundary

- Health, progress, model and sampler inspection are read-only.
- A txt2img/img2img request is an external GPU side effect; submit it only
  when the user has requested generation.
- Do not interrupt, clear, reload models, or change Forge options unless the
  user explicitly asks for that operation.
- Save the returned sidecar JSON beside generated images so the request and
  Forge response remain reproducible.

Read [references/api.md](references/api.md) for the method matrix and payload
details when an operation is not covered by the short example. The preflight
helper lives in [scripts/forge_preflight.py](scripts/forge_preflight.py).
