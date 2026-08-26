# Norual Agent ⚡︎

Your personal agentic CLI — a custom fork of
[Hermes Agent](https://hermes-agent.nousresearch.com) (by Nous Research),
rebranded and tuned for one user: you.

**Norual Agent** is a terminal AI agent that reads your files, runs commands,
edits code, searches the web, remembers things across sessions, and can talk
to any OpenAI-compatible provider (OpenRouter, DeepSeek, Anthropic, Gemini,
Ollama, LM Studio, …). It works as an interactive chat, a one-shot CLI
(`norual -z "task"`), a coding pairing tool, and a general assistant — all in
one binary.

## What's special about this fork

- **Norual branding everywhere** — red/maroon hacker skin, banner, model-facing
  identity (`SOUL.md`), version strings
- **`norual provider` / `/provider`** — pick a provider from a menu, paste your
  API key (masked), done; `--remove` deletes a provider's credentials
- **`/model`** opens the current provider's model list; **`/models`** lets you
  switch providers first (configured providers only)
- **`NORUAL.md`** — a fork-native project instructions file, loaded *ahead of*
  `AGENTS.md`/`CLAUDE.md`
- **Live pulsing bolt spinner** while the agent thinks
- **Model switches persist by default** (`model.persist_switch_by_default`)
- **Coding/chat flavor presets** in [`presets/`](presets/)
- Upstream compatibility preserved: the `hermes` binary still exists because
  skills and internal tooling call it by name — but **you always type `norual`**

## Requirements

- Linux or macOS (Windows via WSL2)
- `git`, `curl`
- `uv` — install with `curl -LsSf https://astral.sh/uv/install.sh | sh`
- An LLM API key (OpenRouter, DeepSeek, Anthropic, …)

## Installation

```bash
git clone https://github.com/lauronjohn/norual-agent.git
cd norual-agent

# install uv (if you don't have it)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# create a venv (outside the repo, so the agent never wipes its own runtime)
uv venv ~/.norual/venvs/norual-dev --python 3.11
source ~/.norual/venvs/norual-dev/bin/activate
uv pip install -e ".[all,dev]"

# put `norual` on your PATH (new terminals only)
echo 'export PATH="$HOME/.norual/venvs/norual-dev/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## First-run setup

```bash
norual provider          # pick a provider from the menu → paste your API key
```

Keys are stored in `~/.norual/.env` (secrets only — never committed).
Providers with a key show as `configured`; without one, `no key`.

You can also edit the files directly:

- `~/.norual/.env` — API keys
  ```
  OPENROUTER_API_KEY=sk-or-v1-...
  DEEPSEEK_API_KEY=sk-...
  ```
- `~/.norual/config.yaml` — settings (see below)

## Usage

```bash
norual                    # interactive chat (resumes your last session)
nra                       # same thing, shorter
norual -z "fix the failing test"          # one-shot, prints only the answer
norual -m deepseek-v4-flash --provider deepseek -z "hi"
norual --tui              # full-screen Ink TUI
```

In-session commands:

| Command | What it does |
|---|---|
| `/help` | all commands |
| `/model` | pick a model from the **current** provider |
| `/models` | pick a **provider** first, then a model |
| `/provider [id]` | add/replace a provider's API key |
| `/provider --remove <id>` | remove a provider's credentials |
| `/skin` | switch themes (`norual`, `default`, `ares`, …) |
| `/skills` | browse the ~77 bundled skills (arxiv, plan, …) |
| `/tools` | enable/disable toolsets |
| `/quit` | exit |

## Configuration (`~/.norual/config.yaml`)

```yaml
model:
  provider: openrouter        # default provider
  default: deepseek/deepseek-v4-flash
  persist_switch_by_default: true   # /model switches stick for next launch

display:
  skin: norual

agent:
  coding_context: auto        # coding posture in code workspaces
  coding_instructions: "..."

security:
  approvals:
    mode: smart               # auto-approve read-only commands
```

Flavor presets (copy one over your config): `presets/coding.yaml` and
`presets/chat.yaml`.

## Project instructions

Norual honors per-project instruction files, in priority order:

`NORUAL.md` → `.hermes.md`/`HERMES.md` → `AGENTS.md` (git-root chain) →
`CLAUDE.md` → `.cursorrules`

Drop a `NORUAL.md` in any project to give the agent your conventions there.

## Development

```bash
source ~/.norual/venvs/norual-dev/bin/activate
scripts/run_tests.sh tests/hermes_cli/        # always use the wrapper, never bare pytest
```

- `NORUAL_NOTES.md` — every fork-side patch is tracked here (re-apply notes
  for upstream merges)
- Branch layout: **`norual`** = all custom work · **`main`** = pristine
  upstream tracking
- Upstream: `git fetch upstream` (NousResearch/hermes-agent) — merge
  deliberately, use `NORUAL_NOTES.md` as the checklist

## Notes

- The `hermes` / `hermes-agent` binaries are compatibility aliases —
  skills' instructions invoke them by name. Ignore them; `norual` is yours.
- Upstream documentation at <https://hermes-agent.nousresearch.com/docs>
  applies to this fork (same engine), minus the branding.
