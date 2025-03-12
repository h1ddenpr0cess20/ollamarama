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
ollama pull qwen2.5:14b  # or any other model you prefer
```

4. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Edit the `config.json` file to customize your setup:

## Usage

Run the application:
```bash
python3 ollamarama.py
```

Start chatting with the AI, or use commands to customize the experience.

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
* `/temperature`: Changes temperature setting
* `/top_p`: Changes top_p setting
* `/repeat_penalty`: Changes repeat_penalty setting
* `/quit` or `/exit`: Exits the program

**Tip:** Use Esc+Enter to input multiple lines of text.

