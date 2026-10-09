"""Image-to-video generator powered by the Hugging Face Inference API.

Takes a still image (default: cat.png) and a text prompt, then asks an
image-to-video model to animate it. The resulting video is written to disk.

Usage:
    python app.py
    python app.py --image cat.png --prompt "The cat starts to dance" --output cat.mp4
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from huggingface_hub import InferenceClient

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # python-dotenv is optional
    pass


try:
    from huggingface_hub.inference._providers._common import (
        _fetch_inference_provider_mapping,
    )
    from huggingface_hub.inference._providers.fal_ai import FalAIImageToVideoTask

    _HAVE_FALLBACK = True
except ImportError:  # private API moved/removed in a future hub release
    _HAVE_FALLBACK = False


DEFAULT_IMAGE = "cat.png"
DEFAULT_PROMPT = "The cat starts to dance"
DEFAULT_MODEL = "MiniMaxAI/MiniMax-H3"
DEFAULT_PROVIDER = "fal-ai"


def _build_image_to_video_fallback(provider: str):
    """Return a helper for models registered under the `image-text-to-video`
    task, which `InferenceClient.image_to_video` does not recognize.

    Example: MiniMaxAI/MiniMax-H3 is exposed by fal-ai as
    `minimax/h3/image-to-video` with task `image-text-to-video`. The request
    shape is identical to a normal image-to-video call, so we reuse the
    library's fal-ai image-to-video helper and only relax the task check.
    """
    if provider != "fal-ai" or not _HAVE_FALLBACK:
        return None

    class _ImageTextToVideoTask(FalAIImageToVideoTask):
        def _prepare_mapping_info(self, model):
            for mapping in _fetch_inference_provider_mapping(model):
                if mapping.provider == self.provider:
                    return mapping
            raise ValueError(f"Model {model} is not supported by provider {self.provider}.")

    return _ImageTextToVideoTask()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Animate a still image into a short video using Hugging Face.",
    )
    parser.add_argument(
        "--image",
        default=DEFAULT_IMAGE,
        help=f"Path to the input image (default: {DEFAULT_IMAGE}).",
    )
    parser.add_argument(
        "--prompt",
        default=DEFAULT_PROMPT,
        help="Text prompt describing the motion (default: %(default)r).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output video path (default: <image stem>.mp4).",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Hub model id (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--provider",
        default=DEFAULT_PROVIDER,
        help=f"Inference provider (default: {DEFAULT_PROVIDER}).",
    )
    return parser.parse_args(argv)


def read_image(image_path: Path) -> bytes:
    if not image_path.is_file():
        raise FileNotFoundError(
            f"Input image not found: {image_path}\n"
            f"Place a '{DEFAULT_IMAGE}' next to this script or pass --image <path>."
        )
    data = image_path.read_bytes()
    if not data:
        raise ValueError(f"Input image is empty: {image_path}")
    return data


def generate_video(
    client: InferenceClient,
    image_bytes: bytes,
    prompt: str,
    model: str,
    provider: str,
) -> bytes:
    try:
        return client.image_to_video(image_bytes, prompt=prompt, model=model)
    except ValueError as exc:
        if "not supported for task" not in str(exc):
            raise

        # The model uses the `image-text-to-video` task, which the high-level
        # method cannot route. Fall back to a direct provider call.
        helper = _build_image_to_video_fallback(provider)
        if helper is None:
            raise

        request = helper.prepare_request(
            inputs=image_bytes,
            parameters={"prompt": prompt},
            headers={},
            model=model,
            api_key=client.token,
        )
        response = client._inner_post(request)
        return helper.get_response(response, request)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    api_key = os.environ.get("HF_TOKEN")
    if not api_key:
        print(
            "Error: the HF_TOKEN environment variable is not set.\n"
            "Create a token at https://huggingface.co/settings/tokens, then "
            "export HF_TOKEN=... or put it in a .env file (see .env.example).",
            file=sys.stderr,
        )
        return 1

    image_path = Path(args.image)
    output_path = Path(args.output) if args.output else image_path.with_suffix(".mp4")

    try:
        input_image = read_image(image_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    client = InferenceClient(provider=args.provider, api_key=api_key)

    print(f"Animating {image_path} with '{args.model}' ...")
    try:
        video = generate_video(client, input_image, args.prompt, args.model, args.provider)
    except Exception as exc:  # surface provider/network errors clearly
        print(f"Error: video generation failed: {exc}", file=sys.stderr)
        return 1

    if not video:
        print("Error: the API returned an empty video.", file=sys.stderr)
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(video)
    print(f"Saved video to {output_path} ({len(video):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
