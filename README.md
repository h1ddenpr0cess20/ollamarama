# Ollamarama

![License](https://img.shields.io/github/license/h1ddenpr0cess20/ollamarama)

A terminal-based AI chatbot with infinite personalities, powered by local LLMs through Ollama. Create, customize, and chat with AI personalities directly from your terminal.

Also available for:
- [IRC](https://github.com/h1ddenpr0cess20/ollamarama-irc)
- [Matrix](https://github.com/h1ddenpr0cess20/ollamarama-matrix)

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Docker](#docker)
- [Commands](#commands)
- [License](#license)

## Features

- Chat with locally-hosted LLMs using Ollama
- Create unlimited custom AI personalities
- Adjust model parameters like temperature and top_p on the fly
- Switch between different AI models
- Multi-line input support (Esc+Enter)
- Rich markdown rendering for AI responses
- Customizable system prompts

## Prerequisites

- Python 3.7 or higher
- [Ollama](https://ollama.com/) installed and running
- At least one LLM model pulled via Ollama

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

3. Pull at least one model using Ollama:
```bash
ollama pull qwen3  # or any other model you prefer
```

4. Install in editable mode (recommended for local use):
```bash
pip install -e .
```

## Configuration

Edit the `config.json` file to customize your setup:

## Usage

Run the application:
```bash
# As a module
python -m ollamarama

# Or via the CLI entrypoint after install
ollamarama
```

You can also pass basic flags to start with specific settings:

```bash
# Choose a model by key or full name
ollamarama --model qwen3      # uses key from config.json
ollamarama --model qwen3:latest  # uses full model name directly

# Start with a custom persona or stock settings
ollamarama --persona "a terse unix greybeard"
ollamarama --stock

# Override generation options
ollamarama --temperature 0.4 --top-p 0.9 --repeat-penalty 1.1

# Point to a different Ollama API base
ollamarama --api-base http://localhost:11434
```

Start chatting with the AI, or use commands to customize the experience.

## Docker

- Build image:
  - `docker build -t ollamarama .`

- Run against a host Ollama daemon (Linux):
  - `docker run -it --rm --name ollamarama \
     --add-host=host.docker.internal:host-gateway \
     -v "$(pwd)/config.json:/app/config.json:ro" \
     ollamarama --api-base http://host.docker.internal:11434`

- Run with Docker Compose (spins up Ollama + app):
  - `docker compose up -d ollama` (first time pulls models separately via `docker exec -it ollama ollama pull qwen3`)
  - `docker compose run --rm app` (interactive chat; add flags like `--model qwen3` as needed)

Notes:
- The TUI is interactive; always use `-it` or `docker compose run` (not `up`) for the `app` service.
- Copy-to-clipboard depends on the host; it may be unavailable inside the container.
- To use a different API base, append flags after the image name, e.g. `--api-base http://ollama:11434` in Compose.

## Commands

**Commands**

* `/help`: Shows the help menu
* `/reset`: Resets to default personality
* `/clear`: Resets and clears the screen
* `/stock`: Sets bot to stock model settings
* `/persona`: Activates personality changer (prompts for new personality)
* `/custom`: Use a custom system prompt
* `/model`: List models and change the current model
* `/model reset`: Reset to default model
* `/copy`: Copies the last bot response to clipboard
* `/tools`: Enables or disables tool use
* `/temperature`: Changes temperature setting
* `/top_p`: Changes top_p setting
* `/repeat_penalty`: Changes repeat_penalty setting
* `/quit` or `/exit`: Exits the program

**Tip:** Use Esc+Enter to input multiple lines of text.
