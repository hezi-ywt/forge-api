"""Command-line entry points for ForgeAPI."""

from __future__ import annotations

import argparse
import sys

from . import ForgeClient, ForgeError


def preflight(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Forge without generating")
    parser.add_argument("--url", default=None, help="Forge URL or host:port")
    args = parser.parse_args(argv)
    try:
        client = ForgeClient(args.url) if args.url else ForgeClient()
        progress = client.progress()
        print(f"Forge: {client.url}")
        print(f"progress: {progress.get('progress', 0)}")
        options = client.options()
        print(f"checkpoint: {options.get('sd_model_checkpoint', '<unknown>')}")
        print("endpoints: progress, options, samplers, loras, checkpoints, vaes, txt2img, img2img")
        return 0
    except (ForgeError, ValueError) as exc:
        print(f"Forge preflight failed: {exc}", file=sys.stderr)
        return 2


def main() -> int:
    return preflight()


if __name__ == "__main__":
    raise SystemExit(main())
