"""Dependency-free REST client for Stable Diffusion WebUI Forge."""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Protocol
from typing import Any

from .outputs import GenerationResult
from .units import ADetailerConfig, IPAUnit


class ForgeError(RuntimeError):
    """Forge request failed or returned an unexpected response."""


class ForgePreset(Protocol):
    """Minimal preset contract accepted by the client."""

    def forge_payload(self) -> dict[str, Any]: ...


@dataclass(frozen=True)
class ForgeConfig:
    """Connection settings independent of any project configuration."""

    url: str = "http://127.0.0.1:7860"
    timeout: int = 900
    auth_token: str | None = None

    def normalized_url(self) -> str:
        return _url(self.url)


def _url(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("Forge URL cannot be empty")
    if "://" not in value:
        value = "http://" + value
    if not value.startswith(("http://", "https://")):
        raise ValueError(f"invalid Forge URL: {value!r}")
    return value.rstrip("/")


@dataclass
class ForgeClient:
    """Client for Forge's REST endpoints.

    ``url`` may be a full URL or a host:port.  The environment variable
    ``AUTOMUSE_FORGE_URL`` overrides the default localhost URL.
    """

    url: str = "http://127.0.0.1:7860"
    timeout: int = 900
    auth_token: str | None = None

    def __post_init__(self) -> None:
        if self.url == "http://127.0.0.1:7860":
            self.url = os.environ.get("AUTOMUSE_FORGE_URL", self.url)
        self.url = _url(self.url)
        if self.timeout <= 0:
            raise ValueError("Forge timeout must be positive")

    def _request(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        data = None if payload is None else json.dumps(payload).encode()
        headers = {"Content-Type": "application/json"} if data else {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        request = urllib.request.Request(
            self.url + path,
            data=data,
            headers=headers,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.load(response)
        except Exception as exc:
            raise ForgeError(f"Forge request failed ({path}): {exc}") from exc

    def progress(self) -> dict[str, Any]:
        return self._request("/sdapi/v1/progress")

    def options(self) -> dict[str, Any]:
        return self._request("/sdapi/v1/options")

    def samplers(self) -> list[dict[str, Any]]:
        return self._request("/sdapi/v1/samplers")

    def loras(self) -> list[dict[str, Any]]:
        return self._request("/sdapi/v1/loras")

    def checkpoints(self) -> list[dict[str, Any]]:
        return self._request("/sdapi/v1/sd-models")

    def vaes(self) -> list[dict[str, Any]]:
        return self._request("/sdapi/v1/sd-vae")

    def controlnet_models(self) -> list[str]:
        return self._request("/controlnet/model-list")

    def adetailer_models(self) -> list[str]:
        return self._request("/adetailer/v1/ad-models")

    def txt2img(self, *, prompt: str, negative_prompt: str = "", preset: Any = None,
                controlnet: list[IPAUnit] | None = None,
                adetailer: ADetailerConfig | None = None, seed: int = -1,
                batch_size: int = 1, n_iter: int = 1, extra: dict[str, Any] | None = None,
                **parameters: Any) -> GenerationResult:
        return self._generate("/sdapi/v1/txt2img", prompt=prompt,
                              negative_prompt=negative_prompt, preset=preset,
                              controlnet=controlnet, adetailer=adetailer, seed=seed,
                              batch_size=batch_size, n_iter=n_iter, extra=extra,
                              parameters=parameters)

    def img2img(self, *, init_images: list[str], prompt: str, negative_prompt: str = "",
                preset: Any = None, controlnet: list[IPAUnit] | None = None,
                adetailer: ADetailerConfig | None = None, extra: dict[str, Any] | None = None,
                **parameters: Any) -> GenerationResult:
        return self._generate("/sdapi/v1/img2img", prompt=prompt,
                              negative_prompt=negative_prompt, preset=preset,
                              controlnet=controlnet, adetailer=adetailer, extra=extra,
                              parameters={"init_images": init_images, **parameters})

    def _generate(self, path: str, *, prompt: str, negative_prompt: str, preset: Any,
                  controlnet: list[IPAUnit] | None, adetailer: ADetailerConfig | None,
                  seed: int = -1, batch_size: int = 1, n_iter: int = 1,
                  extra: dict[str, Any] | None, parameters: dict[str, Any]) -> GenerationResult:
        payload: dict[str, Any] = {"prompt": prompt, "negative_prompt": negative_prompt,
                                   "seed": seed, "batch_size": batch_size, "n_iter": n_iter}
        if preset is not None:
            payload.update(preset.forge_payload())
        payload.update(parameters)
        alwayson: dict[str, Any] = {}
        if controlnet:
            alwayson["ControlNet"] = {"args": [unit.to_dict() for unit in controlnet]}
        if adetailer:
            alwayson["ADetailer"] = {"args": [True, adetailer.to_dict()]}
        if alwayson:
            payload["alwayson_scripts"] = alwayson
        if extra:
            payload.update(extra)
        data = self._request(path, payload)
        if not isinstance(data, dict) or not data.get("images"):
            raise ForgeError(f"unexpected Forge response: {str(data)[:500]}")
        raw_info = data.get("info", "")
        try:
            info = json.loads(raw_info) if raw_info else {}
        except json.JSONDecodeError:
            info = {"raw": raw_info}
        return GenerationResult(images_b64=data["images"], info=info, payload=payload)
