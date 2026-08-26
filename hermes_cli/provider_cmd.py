"""norual provider — pick a provider, then save your API key.

Fork-native convenience command: lists the API-key providers the agent can
talk to, lets you pick one (curses menu), prompts for the key (masked), writes
it to the profile's .env via the standard credential path, and optionally sets
it as the default provider.

Usage:
    norual provider                # interactive: pick provider → enter key
    norual provider deepseek       # skip the picker
    norual provider --list         # print providers + config status, no prompts
"""

from __future__ import annotations

import getpass
import os
import sys
from typing import Dict, Optional

from hermes_cli.auth import PROVIDER_REGISTRY, ProviderConfig


def _api_key_providers() -> Dict[str, ProviderConfig]:
    """Providers that authenticate with a plain API key (no OAuth flow).

    Merges two sources:
    1. ``PROVIDER_REGISTRY`` (auth.py) — deduped by the entry's canonical
       ``id`` (the provider-plugin scan can register several legacy alias
       keys, e.g. ``meta``/``muse``/``msl``, all resolving to one provider).
    2. ``providers`` plugin profiles — OpenRouter and friends are
       deliberately NOT in the registry (``openrouter not in
       PROVIDER_REGISTRY`` is load-bearing for runtime_provider), but they
       still take a plain API key, so they belong in the picker.
    """
    out: Dict[str, ProviderConfig] = {}

    for pid, cfg in PROVIDER_REGISTRY.items():
        if getattr(cfg, "auth_type", "") != "api_key":
            continue
        if not getattr(cfg, "api_key_env_vars", ()):
            continue
        canonical = getattr(cfg, "id", None) or pid
        out[canonical] = cfg

    try:
        from providers import list_providers as _list_providers

        for pp in _list_providers():
            if getattr(pp, "auth_type", "") != "api_key":
                continue
            env_vars = tuple(
                v for v in getattr(pp, "env_vars", ()) or ()
                if not v.endswith(("_BASE_URL", "_URL"))
            )
            if not env_vars:
                continue
            canonical = str(getattr(pp, "name", "") or "")
            if not canonical or canonical in out:
                continue
            out[canonical] = ProviderConfig(
                id=canonical,
                name=str(getattr(pp, "display_name", None) or canonical),
                auth_type="api_key",
                inference_base_url=str(getattr(pp, "base_url", "") or ""),
                api_key_env_vars=env_vars,
                base_url_env_var=next(
                    (v for v in (getattr(pp, "env_vars", ()) or ())
                     if v.endswith(("_BASE_URL", "_URL"))),
                    "",
                ),
            )
    except Exception:
        pass

    return out


def _resolve_provider_config(pid: str) -> Optional[ProviderConfig]:
    """Resolve a provider id against the registry, then plugin profiles."""
    cfg = PROVIDER_REGISTRY.get(pid)
    if cfg is not None:
        return cfg
    return _api_key_providers().get(pid)


def _env_value(var: str) -> str:
    """Read a var from the profile's .env.

    Subcommands don't load .env into os.environ, so os.getenv alone would
    report "no key" for an already-configured provider. get_env_path() is
    profile-aware (respects HERMES_HOME / the fork's ~/.norual default).
    """
    try:
        from hermes_cli.config import get_env_path

        path = get_env_path()
        if path and path.exists():
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if line.startswith(f"{var}="):
                    return line[len(var) + 1 :].strip().strip('"').strip("'")
    except Exception:
        pass
    return ""


def _status_line(cfg: ProviderConfig) -> str:
    var = cfg.api_key_env_vars[0]
    configured = bool(os.getenv(var) or _env_value(var))
    marker = "configured" if configured else "no key"
    base = getattr(cfg, "inference_base_url", "") or ""
    return f"{cfg.name} [{cfg.id}] — {var} ({marker})" + (f" — {base}" if base else "")


def _prompt_api_key(cfg: ProviderConfig) -> Optional[str]:
    var = cfg.api_key_env_vars[0]
    existing = os.getenv(var) or _env_value(var)
    if existing:
        shown = existing[:10] + "…" if len(existing) > 12 else "(set)"
        print(f"  {cfg.name} already has a key ({shown}) — press Enter to keep it, or type a new one.")
    try:
        raw = getpass.getpass(f"  {cfg.name} API key ({var}): ").strip()
    except (EOFError, KeyboardInterrupt):
        return None
    return raw or None  # empty → keep existing


def _set_default_provider(pid: str) -> None:
    try:
        from hermes_cli.config import set_config_value

        set_config_value("model.provider", pid)
        print(f"✓ default provider set to '{pid}' (config.yaml model.provider)")
    except Exception as e:
        print(f"✗ could not set default provider: {e}", file=sys.stderr)


def _save_key(cfg: ProviderConfig, value: str) -> bool:
    var = cfg.api_key_env_vars[0]
    try:
        from hermes_cli.config import save_env_value

        save_env_value(var, value)
        return True
    except Exception as e:
        print(f"✗ could not save {var}: {e}", file=sys.stderr)
        return False


def _interactive_flow(pid: str, *, key_callback=None, ask_default: bool = True) -> int:
    cfg = _resolve_provider_config(pid)
    if cfg is None:
        print(f"✗ unknown provider '{pid}'. Run `norual provider --list` to see the available ones.",
              file=sys.stderr)
        return 1

    print(_status_line(cfg))

    if key_callback is not None:
        # In-app flow (e.g. /provider inside the interactive CLI): the
        # callback owns prompting + storing (secure modal, no getpass race).
        if not key_callback(cfg):
            return 0
    else:
        var = cfg.api_key_env_vars[0]
        if os.getenv(var) or _env_value(var):
            print(f"  {cfg.name} is already configured — keeping the existing key.")
        else:
            key = _prompt_api_key(cfg)
            if key is None:
                print("(cancelled — nothing changed)")
                return 0
            if not key:
                print("✗ no key entered and none configured.", file=sys.stderr)
                return 1
            if not _save_key(cfg, key):
                return 1
            from hermes_constants import display_hermes_home

            print(f"✓ {var} saved to {display_hermes_home()}/.env")

    if ask_default:
        try:
            choice = input("  Set as default provider? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            choice = "n"
        if choice in ("y", "yes"):
            _set_default_provider(pid)

    print(f"\nNext: `norual model` to pick a model, or `norual -m <model> --provider {pid} -z \"hi\"`.")
    return 0


def _list_flow() -> int:
    providers = _api_key_providers()
    if not providers:
        print("No API-key providers found.")
        return 1
    for pid in sorted(providers, key=lambda p: providers[p].name.lower()):
        print("  " + _status_line(providers[pid]))
    print(f"\n{len(providers)} API-key providers. Configure one with: norual provider <id>")
    return 0


def provider_command(args, *, key_callback=None, ask_default: bool = True) -> int:
    """Dispatch for the `provider` subcommand.

    ``key_callback`` and ``ask_default`` let in-app callers (the /provider
    slash command) substitute the getpass/input prompts with the CLI's own
    secure modal prompts, which are safe inside the running prompt_toolkit
    app (getpass races the app's input reader there).
    """
    if getattr(args, "provider_list", False):
        return _list_flow()

    if getattr(args, "provider_id", None):
        return _interactive_flow(
            args.provider_id, key_callback=key_callback, ask_default=ask_default
        )

    # No positional → interactive picker (curses menu, fallback to numbered).
    providers = _api_key_providers()
    if not providers:
        print("No API-key providers found.", file=sys.stderr)
        return 1
    ids = sorted(providers, key=lambda p: providers[p].name.lower())
    labels = [_status_line(providers[pid]) for pid in ids]

    try:
        from hermes_cli.curses_ui import curses_single_select

        idx = curses_single_select(
            "Select a provider to configure",
            labels,
            searchable=True,
        )
    except Exception:
        idx = None
        for i, label in enumerate(labels, start=1):
            print(f"  {i:>2}. {label}")
        try:
            raw = input("Provider number (0 to cancel): ").strip()
        except (EOFError, KeyboardInterrupt):
            raw = ""
        if raw.isdigit() and 1 <= int(raw) <= len(ids):
            idx = int(raw) - 1
    if idx is None or not (0 <= idx < len(ids)):
        print("(cancelled)")
        return 0
    return _interactive_flow(
        ids[idx], key_callback=key_callback, ask_default=ask_default
    )


def build_parser(subparsers):
    """Register the `provider` subcommand (wired by hermes_cli/main.py)."""
    parser = subparsers.add_parser(
        "provider",
        help="Pick a provider and save its API key",
        description=(
            "Pick an inference provider and enter its API key. The key is "
            "saved to the profile's .env via the standard credential path; "
            "optionally sets it as the default provider."
        ),
    )
    parser.add_argument(
        "provider_id",
        nargs="?",
        help="Provider id to configure directly (skip the picker)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="provider_list",
        help="List all API-key providers and their configuration status",
    )
    return parser
