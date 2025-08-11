# Repository Guidelines

## Project Structure & Module Organization
- `ollamarama/`: core package.
  - `app.py`: runtime loop, command handling, logging.
  - `cli.py`: CLI entry (`ollamarama`), arg parsing and overrides.
  - `client.py`: HTTP client for Ollama `/api/chat`.
  - `config.py`: dataclasses + `load_config` for `config.json`.
  - `render.py`: Rich console and helpers.
  - `sessions.py`: prompt_toolkit sessions and keybindings.
- `ollamarama.py`: module launcher (`python -m ollamarama`).
- `config.json`: runtime config (models, api_base, options).
- `help.txt`: in-app command reference. Logs write to `ollamarama.log`.

## Build, Test, and Development Commands
- `pip install -e .`: install in editable mode.
- `python -m ollamarama`: run as a module.
- `ollamarama --model qwen3 --stock`: run via script with overrides.
- `ollamarama --api-base http://localhost:11434`: point at a different Ollama.
Notes: A formal test suite is not yet configured; see Testing Guidelines.

## Coding Style & Naming Conventions
- Python 3.8+ with type hints; 4‑space indentation.
- Names: snake_case for functions/vars, PascalCase for classes, modules lowercase.
- Imports: standard library, third‑party, local; keep groups separated.
- Use f‑strings, keep functions small and focused, prefer explicit over clever.
- Logging: use `logging` (app writes to `ollamarama.log`); avoid print in core logic.

## Testing Guidelines
- Manual smoke test: `ollamarama --stock`, send a prompt, try `/help`, `/model`, and option commands; verify responses and no tracebacks.
- Ollama integration requires a running daemon and a pulled model (see README).
- If adding tests, place them under `tests/`, name files `test_*.py`, and prefer `pytest` with fast, isolated units (mock HTTP when possible).

## Commit & Pull Request Guidelines
- Commits: short, imperative subject lines (e.g., "fix input handling", "add help text"); keep related changes together.
- PRs: clear description, rationale, and scope; link issues; include repro steps and terminal output/screenshot for user‑visible changes; update README/help/config if behavior or flags change.

## Security & Configuration Tips
- Do not hardcode secrets; prefer `config.json` or CLI flags.
- Keep `config.json` minimal and portable; use `--api-base` locally instead of committing machine‑specific URLs.
