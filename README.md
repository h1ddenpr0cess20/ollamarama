# Ollamarama

![License](https://img.shields.io/github/license/h1ddenpr0cess20/ollamarama)

A terminal-based AI chatbot with infinite personalities, powered by local LLMs through Ollama. Create, customize, and chat with AI personalities directly from your terminal. Optional tool calling via MCP (Model Context Protocol) servers or a bundled tool schema.

Also available for:
- [IRC](https://github.com/h1ddenpr0cess20/ollamarama-irc)
- [Matrix](https://github.com/h1ddenpr0cess20/ollamarama-matrix)

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Tools and MCP Integration](#tools-and-mcp-integration)
- [Docker](#docker)
- [Commands](#commands)
- [License](#license)

## Features

- Chat with locally-hosted LLMs using Ollama
- Unlimited custom AI personalities (or stock/no-persona mode)
- Adjust model parameters (temperature, top_p, repeat_penalty) on the fly
- Switch between different AI models, using friendly keys from config.json
- Tool calling:
  - Auto-discovers tools from configured MCP servers (via `fastmcp`) and merges them with a bundled `tools/schema.json`
  - Toggle at runtime with `/tools`
- Safe streaming that hides any content inside \<think\>...\</think\> blocks
- Multi-line input support (Esc+Enter)
- Rich Markdown rendering for AI responses
- Copy last response to clipboard
- Docker and Docker Compose supported

## Prerequisites

- Python 3.8 or higher
- [Ollama](https://ollama.com/) installed and running
- At least one LLM model pulled via Ollama
- Optional: One or more MCP servers

## Installation

1. Clone the repository:
```bash
git clone https://github.com/h1ddenpr0cess20/ollamarama.git
cd ollamarama
```

2. Install [Ollama](https://ollama.com/) if you haven't already:
```bash
curl https://ollama.com/install.sh | sh
```
(Refer to Ollama docs for Windows/macOS installers.)

3. Pull at least one model using Ollama:
```bash
ollama pull qwen3  # or any other model you prefer
```

4. Install in editable mode (recommended for local use):
```bash
pip install -e .
```

## Configuration

Ollamarama reads a `config.json` from your current working directory. Use it to set your model mapping, defaults, persona, and optional MCP servers.

Example:
```json
{
  "api_base": "http://localhost:11434",
  "options": {
    "temperature": 0.7,
    "top_p": 0.9,
    "repeat_penalty": 1.0
  }
  "default_model": "gpt-oss",
  "prompt": [
    "you are ",
    ". speak in the first person and never break character. keep your responses relatively brief and to the point."
  ],
  "personality": "an open source AI chatbot named Ollamarama, powered by Ollama.",
  "mcp_servers": {
    "playwright": "http://localhost:8931/mcp",
    "notes": {"command": "python", "args": ["notes_server.py"]},
    "browser": {"command": "npx -y @modelcontext/browser"}
  }
}
```

Field reference:
- `api_base`: URL for the Ollama API (default `http://localhost:11434`)
- `options`:
  - `temperature` (0–1)
  - `top_p` (0–1)
  - `repeat_penalty` (0–2)
- `models`: Map friendly keys to actual Ollama model names/tags. Use these keys with `--model` or the `/model` command.
- `default_model`: Key from `models` to select on startup.
- `prompt`: Two-element array `[prefix, suffix]` used to build a persona system prompt (prefix + personality + suffix).
- `personality`: Default personality string used at startup. Use `/stock` to clear or `/persona` to change during a session.
- `mcp_servers`: Optional map of server names to MCP server definitions. Each value may be a URL string or an object with a
  `command` and optional `args` to launch a server via stdio. If `args` is omitted and the `command` string contains
  spaces, it is automatically split into the executable and its arguments. When present, tools are auto-discovered at startup.

Note: If no MCP servers are reachable, Ollamarama falls back to a bundled tool schema at `ollamarama/tools/schema.json`. If neither is available, tool calling is disabled automatically.

## Usage

Run the application:
```bash
# As a module
python -m ollamarama

# Or via the CLI entrypoint (after install)
ollamarama
```

You can also pass flags to start with specific settings:
```bash
# Choose a model by key or full name
ollamarama --model qwen3          # uses key from config.json
ollamarama --model qwen3:latest   # uses full model name directly

# Start with a custom persona or stock settings
ollamarama --persona "a terse unix greybeard"
ollamarama --stock

# Override generation options
ollamarama --temperature 0.4 --top-p 0.9 --repeat-penalty 1.1

# Point to a different Ollama API base
ollamarama --api-base http://localhost:11434
```

Behavior notes:
- Streaming hides any text emitted before a `</think>` tag to avoid exposing hidden reasoning.
- History is trimmed to keep interactions responsive.
- Use Esc+Enter for multi-line input.

## Tools and MCP Integration

Ollamarama can call tools in the middle of a conversation. This is useful for actions like fetching URLs, running automations, or integrating with local services.

- Enable/disable at runtime: `/tools`
- On startup:
  1. If `mcp_servers` are configured, Ollamarama connects to remote URLs or launches command-based servers via `fastmcp` and
     auto-discovers their tool schemas.
  2. The discovered tools are merged with the bundled schema from `ollamarama/tools/schema.json`. When no MCP servers are reachable, only the bundled schema is used.
  3. If no schema is available, tool calling is disabled.

Example MCP setup:
1. Add your MCP server under `mcp_servers` in `config.json`. Each entry can be a URL or a `{ "command": ..., "args": [...] }`
   spec. If the `command` string already includes arguments, `args` may be omitted and will be split automatically.
2. Start `ollamarama`. Remote servers are connected to and command-based servers are launched automatically. Tools will be
   discovered without extra steps.

Security note: Tool calls can execute actions exposed by your MCP servers. Only connect to servers you trust and understand.

## Docker

- Build image:
```bash
docker build -t ollamarama .
```

- Run against a host Ollama daemon (Linux):
```bash
docker run -it --rm --name ollamarama \
  --add-host=host.docker.internal:host-gateway \
  -v "$(pwd)/config.json:/app/config.json:ro" \
  ollamarama --api-base http://host.docker.internal:11434
```

- Run with Docker Compose (spins up Ollama + app):
```bash
# First time: start Ollama service
docker compose up -d ollama

# Pull models into the running service (example)
docker exec -it ollama ollama pull qwen3

# Start interactive chat (append flags like --model qwen3 as needed)
docker compose run --rm app
```

Notes:
- The TUI is interactive; always use `-it` or `docker compose run` (not `up`) for the `app` service.
- Copy-to-clipboard depends on the host; it may be unavailable inside the container.
- To use a different API base, append flags after the image name, for example `--api-base http://ollama:11434` in Compose.

## Commands

- `/help`: Shows the help menu
- `/reset`: Resets to default personality
- `/clear`: Resets and clears the screen
- `/stock`: Sets bot to stock model settings
- `/persona`: Activates personality changer (prompts for new personality)
- `/custom`: Use a custom system prompt
- `/model`: List models and change the current model
- `/model reset`: Reset to default model
- `/copy`: Copies the last bot response to clipboard
- `/tools`: Enables or disables tool use
- `/temperature`: Changes temperature setting
- `/top_p`: Changes top_p setting
- `/repeat_penalty`: Changes repeat_penalty setting
- `/quit` or `/exit`: Exits the program

Tip: Use Esc+Enter to input multiple lines of text.

## License

Licensed under the terms of the [MIT License](LICENSE).
