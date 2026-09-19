# ForgeAPI capability reference

The shared package is imported as `forge_api` after the consumer project
installs the package into its own virtual environment.

| Capability | Entry point | Side effect |
|---|---|---|
| Health/progress | `ForgeClient.progress()` | read-only |
| Current options | `ForgeClient.options()` | read-only |
| Models and samplers | `checkpoints()`, `loras()`, `vaes()`, `samplers()` | read-only |
| txt2img | `ForgeClient.txt2img(...)` | generates images |
| img2img | `ForgeClient.img2img(...)` | generates images |
| IPA/ControlNet | `IPAUnit` in `controlnet` | generates images |
| ADetailer | `ADetailerConfig` in `adetailer` | generates images |
| Save result | `GenerationResult.save()` | writes local files |

Keep `hr_additional_modules` as an array when Hires fix is enabled. Forge
builds may fail when this field is sent as JSON `null`.
