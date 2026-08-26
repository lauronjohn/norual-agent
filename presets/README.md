# Norual Agent presets

Two ready-to-use flavor presets for `~/.norual/config.yaml`:

| File | Flavor | Effect |
|---|---|---|
| `coding.yaml` | Pair-programming | `agent.coding_context: on`, coding instructions, smart approvals with read-only auto-approve policy |
| `chat.yaml` | General assistant | `agent.coding_context: off`, manual approvals, full general posture |

## Defaults (what your `~/.norual/config.yaml` already uses)

`agent.coding_context: auto` — the best of both: the coding posture engages
automatically in code workspaces (git repo / manifest / `AGENTS.md` /
`NORUAL.md` present) and the general assistant posture applies everywhere
else. Only override with `on`/`off` when you want one flavor pinned.

## Usage

Swap flavors by copying the chosen preset over your config:

```bash
cp presets/coding.yaml ~/.norual/config.yaml   # then add OPENROUTER_API_KEY model
cp presets/chat.yaml   ~/.norual/config.yaml
```

Or merge individual sections into your existing config and re-run `nra`.

## Project instruction files (priority order)

`NORUAL.md` (fork-native) → `.hermes.md`/`HERMES.md` → `AGENTS.md` (git-root
chain) → `CLAUDE.md` → `.cursorrules` — first found wins. `NORUAL.md` is
honored in subdirectory hints and profile exports too.
