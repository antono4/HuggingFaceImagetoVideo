# Image to Video (Hugging Face)

A small command-line app that animates a still image into a short video using the
[Hugging Face Inference API](https://huggingface.co/docs/inference-providers).

It sends an input image plus a text prompt to an image-to-video model (default
`MiniMaxAI/MiniMax-H3` via the `fal-ai` provider) and saves the returned `.mp4`.

## Requirements

- Python 3.9+
- A Hugging Face account and access token: https://huggingface.co/settings/tokens

## Setup

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env   # then edit .env and paste your token
```

Alternatively, export the token directly:

```bash
export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Run

Put your image next to the script (e.g. `cat.png`) and run:

```bash
python app.py
```

This animates `cat.png` with the prompt *"The cat starts to dance"* and writes
`cat.mp4`.

### Options

```bash
python app.py \
  --image path/to/cat.png \
  --prompt "The cat starts to dance" \
  --output cat.mp4 \
  --model MiniMaxAI/MiniMax-H3 \
  --provider fal-ai
```

| Option       | Default                 | Description                          |
| ------------ | ----------------------- | ------------------------------------ |
| `--image`    | `cat.png`               | Input image                          |
| `--prompt`   | `The cat starts to dance` | Text prompt describing the motion  |
| `--output`   | `<image stem>.mp4`      | Output video path                    |
| `--model`    | `MiniMaxAI/MiniMax-H3`  | Hugging Face model id                |
| `--provider` | `fal-ai`                | Inference provider                   |

## No image handy?

Generate a placeholder image to test with:

```bash
pip install pillow
python create_sample_image.py   # writes cat.png
python app.py                   # produces cat.mp4
```

## Models

The default model is `MiniMaxAI/MiniMax-H3`. On the `fal-ai` provider this model
is registered under the task **`image-text-to-video`**, which
`InferenceClient.image_to_video` does not recognize — calling it directly raises:

```
Model MiniMaxAI/MiniMax-H3 is not supported for task image-to-video and provider fal-ai.
Supported task: image-text-to-video.
```

`app.py` handles this transparently: it first tries `client.image_to_video`, and
if the task mismatch is reported it falls back to a direct provider request using
the same image + prompt shape.

If you prefer a model that works with the plain API path, use Alibaba's Wan 2.2:

```bash
python app.py --model Wan-AI/Wan2.2-I2V-A14B
```

## Notes

- Video generation is a paid Inference Provider feature. Billing and model
  availability depend on your Hugging Face account and the selected provider.
- If a model id returns a *not found* error, check that the model is served by
  the chosen provider on the model page (the **Inference Providers** widget).
- The fallback path uses a private helper from `huggingface_hub`
  (`huggingface_hub.inference._providers`). It is pinned by
  `huggingface_hub>=0.34.0`; a future release could move it.
