"""Typed parameter units for Forge generation.

Each unit validates its fields at construction time so that misconfigured
requests fail fast instead of being silently ignored by Forge.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

def _b64_image(path: str | Path) -> str:
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        raise FileNotFoundError(f"reference image not found: {p}")
    return base64.b64encode(p.read_bytes()).decode("ascii")


@dataclass(frozen=True)
class IPAUnit:
    """One ControlNet IP-Adapter unit.

    Defaults match the validated Azuchi baseline (see doc/t2i调参指南).
    The most critical default is ``hr_option='Low res only'`` — Forge's own
    default ('Both') re-fires IPA during the HR second pass and amplifies
    artefacts.
    """

    model: str
    image: str  # base-encoded PNG/JPG
    module: str = "CLIP-ViT-bigG (IPAdapter)"
    weight: float = 0.6
    resize_mode: str = "Crop and Resize"
    processor_res: float = 0.5
    guidance_start: float = 0.0
    guidance_end: float = 0.75
    control_mode: str = "Balanced"
    pixel_perfect: bool = False
    hr_option: str = "Low res only"

    def __post_init__(self) -> None:
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"IPA weight must be in [0,1], got {self.weight}")
        if not 0.0 <= self.guidance_start < self.guidance_end <= 1.0:
            raise ValueError(
                f"need 0 <= guidance_start < guidance_end <= 1, got "
                f"{self.guidance_start}/{self.guidance_end}"
            )
        if self.hr_option not in ("Low res only", "Both", "High res only"):
            raise ValueError(f"invalid hr_option: {self.hr_option!r}")
        if not 0.0 <= self.processor_res <= 2.0:
            # Forge accepts a float multiplier (e.g. 0.5) or absolute pixels.
            raise ValueError(f"processor_res out of range: {self.processor_res}")

    @classmethod
    def from_config(cls, config: Any, image_path: str | Path) -> "IPAUnit":
        """Build an IPAUnit from a preset IPAConfig + reference image."""
        return cls(
            model=config.model,
            image=_b64_image(image_path),
            module=config.module,
            weight=config.weight,
            processor_res=config.processor_res,
            guidance_start=config.guidance_start,
            guidance_end=config.guidance_end,
            resize_mode=config.resize_mode,
            control_mode=config.control_mode,
            pixel_perfect=config.pixel_perfect,
            hr_option=config.hr_option,
        )

    @classmethod
    def from_reference(
        cls,
        image_path: str | Path,
        *,
        model: str,
        weight: float = 0.6,
        guidance_end: float = 0.75,
        processor_res: float = 0.5,
        hr_option: str = "Low res only",
        **kwargs: Any,
    ) -> "IPAUnit":
        """Build an IPAUnit from a reference image file on disk."""
        return cls(
            model=model,
            image=_b64_image(image_path),
            weight=weight,
            guidance_end=guidance_end,
            processor_res=processor_res,
            hr_option=hr_option,
            **kwargs,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": True,
            "module": self.module,
            "model": self.model,
            "weight": self.weight,
            "image": self.image,
            "resize_mode": self.resize_mode,
            "processor_res": self.processor_res,
            "guidance_start": self.guidance_start,
            "guidance_end": self.guidance_end,
            "control_mode": self.control_mode,
            "pixel_perfect": self.pixel_perfect,
            "hr_option": self.hr_option,
        }


@dataclass(frozen=True)
class ADetailerConfig:
    """ADetailer (face repair) configuration."""

    ad_model: str = "face_yolov8n.pt"
    ad_tab_enable: bool = True
    ad_confidence: float = 0.30
    ad_denoising_strength: float = 0.32
    ad_inpaint_only_masked: bool = True
    ad_inpaint_only_masked_padding: int = 32
    ad_restore_face: bool = True
    ad_prompt: str = ""

    def __post_init__(self) -> None:
        if not 0.0 <= self.ad_denoising_strength <= 1.0:
            raise ValueError(
                f"ad_denoising_strength must be in [0,1], "
                f"got {self.ad_denoising_strength}"
            )

    @classmethod
    def face_repair(cls, denoise: float = 0.32, prompt: str = "") -> "ADetailerConfig":
        """Convenience constructor for the standard face-repair pass."""
        return cls(ad_denoising_strength=denoise, ad_prompt=prompt)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ad_model": self.ad_model,
            "ad_tab_enable": self.ad_tab_enable,
            "ad_confidence": self.ad_confidence,
            "ad_denoising_strength": self.ad_denoising_strength,
            "ad_inpaint_only_masked": self.ad_inpaint_only_masked,
            "ad_inpaint_only_masked_padding": self.ad_inpaint_only_masked_padding,
            "ad_restore_face": self.ad_restore_face,
            "ad_prompt": self.ad_prompt,
        }


@dataclass(frozen=True)
class HRConfig:
    """Hires-fix (second-pass) configuration."""

    scale: float = 1.2
    denoise: float = 0.32
    upscaler: str = "R-ESRGAN 4x+ Anime6B"
    second_pass_steps: int = 20
    sampler_name: str = "Euler a"
    scheduler: str = "exponential"

    def __post_init__(self) -> None:
        if self.scale <= 1.0:
            raise ValueError(f"hr_scale must be > 1.0, got {self.scale}")
        if not 0.0 < self.denoise <= 1.0:
            raise ValueError(f"denoise must be in (0,1], got {self.denoise}")

    def to_payload(self) -> dict[str, Any]:
        return {
            "enable_hr": True,
            "hr_scale": self.scale,
            "denoising_strength": self.denoise,
            "hr_upscaler": self.upscaler,
            "hr_second_pass_steps": self.second_pass_steps,
            "hr_sampler_name": self.sampler_name,
            "hr_scheduler": self.scheduler,
            "hr_additional_modules": ["Use same choices"],
        }
