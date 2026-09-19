"""Result object returned by ForgeClient.txt2img."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GenerationResult:
    """Images and metadata from a successful txt2img call."""

    images_b64: list[str]
    info: dict[str, Any]
    payload: dict[str, Any]

    @property
    def image_b64(self) -> str:
        """First image (base64)."""
        return self.images_b64[0]

    @property
    def image_bytes(self) -> bytes:
        """First image decoded to raw bytes."""
        return base64.b64decode(self.image_b64.split(",", 1)[-1])

    @property
    def seed(self) -> int:
        return int(self.info.get("seed", -1))

    @property
    def width(self) -> int:
        return int(self.info.get("width", 0))

    @property
    def height(self) -> int:
        return int(self.info.get("height", 0))

    def save(self, path: str | Path, *, write_parameters: bool = True) -> Path:
        """Save the first image to *path*.

        When *write_parameters* is True (default) a sidecar
        ``<stem>.parameters.json`` is written next to the image containing
        the full request payload and the parsed response info.
        """
        p = Path(path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(self.image_bytes)

        if write_parameters:
            sidecar = p.with_suffix(".parameters.json")
            sidecar.write_text(
                json.dumps(
                    {"payload": self.payload, "info": self.info},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        return p

    def save_all(self, directory: str | Path, *, stem: str = "image") -> list[Path]:
        """Save every image in the batch to *directory*."""
        out = Path(directory).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        paths = []
        for i, b64 in enumerate(self.images_b64):
            p = out / f"{stem}_{i:02d}.png"
            p.write_bytes(base64.b64decode(b64.split(",", 1)[-1]))
            paths.append(p)
        return paths
