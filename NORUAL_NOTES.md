# NORUAL_NOTES.md

Tracking file for norual-agent fork-specific work. Every manual patch we make
that diverges from upstream `NousResearch/hermes-agent` gets an entry here so
re-applying after upstream pulls stays mechanical.

## Setup (Phase 0 — complete)

- Fork: `lauronjohn/norual-agent`, cloned at `~/norual-agent`
- Remotes: `origin` → lauronjohn fork · `upstream` → NousResearch/hermes-agent
- Branch strategy: all custom work on **`norual`**; `main` tracks upstream
- Baseline tag: `norual-baseline` = `1fe0f2f3a` (v0.20.5, 2026.8.19)
- venv: `~/.norual/venvs/norual-dev` (Python 3.11.16), symlinked as repo `.venv`
  so `scripts/run_tests.sh` finds it
- Install: `uv pip install -e ".[all,dev]"`

## Ground rules (from upstream AGENTS.md — binding on us too)

1. ALWAYS test via `scripts/run_tests.sh <path>` — never bare pytest.
2. Never hardcode `~/.hermes` — use `get_hermes_home()` / `display_hermes_home()`.
3. Prompt caching is sacred: no mid-conversation system-prompt rebuilds,
   toolset swaps, or past-context mutations (only exception: compression).
4. Core is a narrow waist — prefer plugins/skills/skins/toolsets over core edits.
5. `config.yaml` for behavior, `.env` only for secrets.
6. New tools need exactly 2 files: `tools/<name>.py` (self-registers) +
   entry in `toolsets.py`. Most capabilities should NOT be core tools.
7. No change-detector tests; tests must not write outside temp HERMES_HOME.

## Manual patches vs upstream

### Phase 1 — identity & defaults (complete)

| File | Change | Re-apply notes |
|---|---|---|
| `hermes_constants.py` | `_get_platform_default_hermes_home()` → `~/.norual` (win: `%LOCALAPPDATA%\norual`) | Default-home change; HERMES_HOME env still wins |
| `pyproject.toml` | `[project.scripts]` + `norual-agent` + `nra` (→ `hermes_cli.main:main`) | Upstream merges of pyproject will need re-adding |
| `hermes_cli/profiles.py` | `_HERMES_CONSOLE_SCRIPT_NAMES` += `norual-agent`, `nra` | So process scans recognize the new shims |
| `hermes_cli/skin_engine.py` | Added built-in `norual` skin (blood red/maroon, hacker spinner, banner logo/hero) | Pure addition — merges clean |
| `hermes_cli/banner.py`, `_startup_fast.py`, `cli.py` | Version label string `Hermes Agent v` → `Norual Agent v` | Display-only |
| `tests/test_hermes_constants.py`, `tests/hermes_cli/test_banner.py`, `tests/hermes_cli/test_apply_profile_override.py` | Expectations updated `.hermes`→`.norual`, `Hermes Agent v`→`Norual Agent v` | Upstream pulls will conflict on these 3 test files — expected |

Not renamed (deliberate): internal modules (`hermes_*`), `HERMES_HOME` env var, `__version__` (update checks depend on it).

### Phase 2 — coding flavor (complete)

| File | Change | Re-apply notes |
|---|---|---|
| `agent/prompt_builder.py` | Added `NORUAL.md`/`norual.md` as priority-0 project context file (walks to git root, ahead of HERMES.md/AGENTS.md); `_find_norual_md` + `_load_norual_md` | Pure addition; upstream merges fine |
| `agent/coding_context.py` | `_PROJECT_MARKERS` + `_CONTEXT_FILES` += `NORUAL.md` (a NORUAL.md-only dir counts as a code workspace) | Pure addition |
| `agent/subdirectory_hints.py` | `_HINT_FILENAMES` += `NORUAL.md`, `norual.md` (first priority) | Pure addition |
| `hermes_cli/profiles.py` | `_DEFAULT_EXPORT_INCLUDE_ROOT` += `NORUAL.md` | Pure addition |
| `presets/` (new) | `coding.yaml`, `chat.yaml`, `README.md` — swap-able flavor configs | New dir |

Assessment (no change needed): the `coding` posture toolset already exists
(`toolsets.py`) and auto-activates in code workspaces (`agent.coding_context:
auto`) with a senior-engineer brief; LSP subsystem is on by default
(`agent.lsp.enabled: true`, on-demand servers, auto-install into HERMES_HOME);
approvals default to `smart` with a custom `smart_policy` hook.

### Phase 3 — assistant flavor (complete)

Config-level only (no code changes):

- `~/.norual/config.yaml` — `memory.*` on (free writes, review via `/memory`),
  `curator.enabled: true` + `consolidate: false` (deterministic maintenance only,
  zero aux cost), `auxiliary.{title_generation,background_review,curator}` routed
  to a cheap OpenRouter flash model (`google/gemini-3-flash-preview`) so
  background LLM work never burns the chat model's budget.
- `presets/coding.yaml` + `presets/chat.yaml` — same assistant block added to
  both presets.

Assessment (no change needed): memory/curator/skills/session-search all ship
enabled with sane defaults; bundled skills are available by default
(`hermes skills` to browse; `hermes skills install official/<cat>/<skill>` for
optional-skills); FTS5 session search is built into `state.db`; cron automations
exist via `hermes cron` / the `cronjob` tool — none created (user preference).

### Phase 3.5 — invoked-name-aware CLI help (complete)

| File | Change | Re-apply notes |
|---|---|---|
| `hermes_cli/_parser.py` | `console_prog()` helper + dynamic `prog=`; description rebranded "Norual Agent - AI assistant..." | Upstream may revert on merge |
| `hermes_cli/console_engine.py` | `_parser_root()` uses `console_prog()` | Same |
| `pyproject.toml`, `_parser.py`, `profiles.py` | Added `norual` as a first-class alias (`norual = "hermes_cli.main:main"`) | Console-script names set ×2 |
| `hermes_cli/oneshot.py` | `run_oneshot` registers the launch directory as the `"default"` task workspace-cwd override (`register_task_env_overrides(..., cwd_source="session")`), mirroring interactive/TUI/ACP/gateway surfaces | Fixes upstream quirk: `norual -z` tools ran in `~` instead of the launch dir |

Why `hermes` still exists (user Q): `norual-agent`/`nra` are aliases to the
same entry point (`hermes_cli.main:main`). The `hermes` binary is kept because
internal machinery invokes it by name — SKILL.md files (`hermes cron`,
`hermes skills install`, ...), process scans
(`_HERMES_CONSOLE_SCRIPT_NAMES`), gateway spawns, cron jobs, docs — and
removing it would break skills and upstream merge hygiene.

### User state (outside repo)
- `~/.norual/skills/` — builtin skills synced via `sync_skills()` (77 enabled),
  incl. `research/arxiv` + `productivity/weekly-review-planning`

## Rebrand inventory (Phase 1 targets)

| Surface | Mechanism | Status |
|---|---|---|
| Display name / agent_name | skin engine: `branding.agent_name` (`hermes_cli/skin_engine.py`) | ✅ done (norual skin) |
| Colors/banner/spinner | custom skin YAML or new built-in skin | ✅ done (built-in `norual`) |
| Home dir | `HERMES_HOME` env / profiles (`~/.norual` via wrapper) | ✅ done (default home changed) |
| Binary name | wrapper script `norual-agent`/`nra` → hermes entrypoint | ✅ done (pyproject scripts) |
| Version label | banner.py / _startup_fast.py / cli.py strings | ✅ done |
| Internal module names | intentionally NOT renamed (upstream merge hygiene) | N/A |
