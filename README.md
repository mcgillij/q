# q — quick CLI assistant

Drop-in CLI helper that pipes questions to a local LLM (OpenAI-compatible endpoint) and streams markdown-formatted answers to your terminal.

## Quickstart

```bash
q "how do I strip audio from a file with ffmpeg?"
```

First time? Pick a model:

```bash
q --list-models       # see what's available
q --set-model          # choose and save a default
```

Then just ask:

```bash
q "list all listening ports with ss"
q -m other-model "find large files with du"
```

## Installation

### via uv (recommended)

```bash
git clone <repo> && cd q
uv tool install --editable .
# now `q` is available everywhere
```

### via pip

```bash
pip install -e .
```

### run without installing

```bash
uv run q "your question"
uv run python -m q "your question"
```

## Usage

```
Usage: q [OPTIONS] [QUERY]...

Options:
  -m, --model TEXT  Model to use (overrides config)
  --list-models     List available models and exit
  --set-model       Interactively set the default model
  --config PATH     Path to config file
  --help            Show this message and exit.
```

### Shell alias

Add to your `.bashrc` / `.zshrc`:

```bash
alias '??'='q'
```

Then:

```bash
?? how to forward ports with ssh?
```

## Configuration

Config is stored at `~/.config/q/config.toml`:

```toml
[server]
base_url = "http://localhost:1234/v1"
model = "qwen3.6-35b-a3b"
api_key = ""

[prompt]
system = "You are a concise, professional Linux and programming assistant..."
```

Override per-run:

```bash
q -m other-model "question"
q --config /path/to/other.toml "question"
```
