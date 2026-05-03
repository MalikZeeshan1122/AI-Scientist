"""Read + safely update the local `.env` file from the in-app Settings page.

This module is a tiny self-contained helper so the settings UI can let users
paste a fresh API key without ever having to drop into a text editor. We
deliberately keep it minimal:

* never echo full secret values back to the client (only a short mask),
* preserve comments + ordering + unrelated keys when writing,
* write atomically (tempfile + os.replace),
* refuse to touch keys outside an explicit allow-list,
* clear the cached `Settings` so the next request reads fresh values.
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Iterable

from .config import get_settings

# Well-known keys we surface in the UI as named providers. Anything else is
# accepted only when it matches the custom-key pattern below (so the user can
# add Cohere / Mistral / DeepSeek / etc. without code changes).
EDITABLE_KEYS: tuple[str, ...] = (
    "ANTHROPIC_API_KEY",
    "GOOGLE_API_KEY",
    "GROQ_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "TAVILY_API_KEY",
    "SEMANTIC_SCHOLAR_API_KEY",
    "AI_SCIENTIST_DEFAULT_PROVIDER",
    "AI_SCIENTIST_ANTHROPIC_MODEL",
    "AI_SCIENTIST_GOOGLE_MODEL",
    "AI_SCIENTIST_GROQ_MODEL",
    "AI_SCIENTIST_OPENAI_MODEL",
    "AI_SCIENTIST_OPENAI_MIN_INTERVAL_S",
    "AI_SCIENTIST_OPENAI_RATE_LIMIT_EXTRA_SLEEP_S",
    "AI_SCIENTIST_OPENROUTER_MODEL",
)
EDITABLE_KEYS_SET = set(EDITABLE_KEYS)

# A user-supplied key must look like a normal env-var name and end in `_API_KEY`
# (or be prefixed `AI_SCIENTIST_` for non-secret config). This blocks shell
# metacharacters, newlines, and accidental targeting of other env vars.
_CUSTOM_API_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,64}_API_KEY$")
_CUSTOM_CONFIG_RE = re.compile(r"^AI_SCIENTIST_[A-Z][A-Z0-9_]{1,64}$")
# Names we will never let the UI overwrite, even if they match the patterns
# above. These are reserved for the runtime / Python tooling.
RESERVED_KEYS: frozenset[str] = frozenset(
    {"PATH", "PYTHONPATH", "PYTHONHOME", "SYSTEMROOT", "USERPROFILE", "HOME"}
)


def is_editable_key(name: str) -> bool:
    """Return True when the key may be written via the Settings API."""
    if not name or name in RESERVED_KEYS:
        return False
    if name in EDITABLE_KEYS_SET:
        return True
    return bool(_CUSTOM_API_KEY_RE.fullmatch(name) or _CUSTOM_CONFIG_RE.fullmatch(name))

# A short non-reversible preview for any secret-shaped value.
def mask_secret(value: str | None) -> str | None:
    if not value:
        return None
    v = value.strip()
    if not v:
        return None
    if len(v) <= 8:
        return "*" * len(v)
    return f"{v[:4]}…{v[-4:]}"


def env_path() -> Path:
    """Resolve the .env file path (sits next to the backend root)."""
    # The backend cwd in dev is `backend/`. Anchor relative to that so we don't
    # accidentally write into the workspace data dir on Windows.
    return Path(".env").resolve()


def read_env_file(path: Path | None = None) -> dict[str, str]:
    """Return a dict of KEY=VALUE pairs from the `.env` file.

    Comments and blank lines are skipped. Values are taken verbatim (we do not
    perform shell-style escape unwrapping; we round-trip exactly what we read).
    """
    p = path or env_path()
    if not p.exists():
        return {}
    out: dict[str, str] = {}
    for raw in p.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        # Strip surrounding quotes if present.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        out[key] = value
    return out


def write_env_updates(
    updates: dict[str, str],
    *,
    path: Path | None = None,
    allowed: Iterable[str] | None = None,
) -> dict[str, str]:
    """Apply ``updates`` to the `.env` file, preserving order + comments.

    Returns the merged final dict. Empty-string values are treated as "unset"
    and remove the key from the file.

    If ``allowed`` is given it acts as an explicit allowlist (legacy behaviour);
    otherwise we accept the well-known keys and any custom ``*_API_KEY`` entry
    that matches :func:`is_editable_key`.
    """
    if allowed is not None:
        allow_set = set(allowed)
        bad = [k for k in updates if k not in allow_set]
    else:
        bad = [k for k in updates if not is_editable_key(k)]
    if bad:
        raise ValueError(f"Refusing to edit non-allowlisted keys: {bad}")

    p = path or env_path()
    p.parent.mkdir(parents=True, exist_ok=True)

    existing_lines: list[str] = (
        p.read_text(encoding="utf-8").splitlines() if p.exists() else []
    )

    seen: set[str] = set()
    new_lines: list[str] = []
    for raw in existing_lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            new_lines.append(raw)
            continue
        key, _, _ = stripped.partition("=")
        key = key.strip()
        if key in updates:
            seen.add(key)
            value = updates[key]
            if value == "":
                # Comment the line out instead of deleting, so the user can see
                # we cleared it on purpose.
                new_lines.append(f"# {key}=  # cleared via Settings UI")
            else:
                new_lines.append(f"{key}={_quote_if_needed(value)}")
        else:
            new_lines.append(raw)

    # Append any keys that weren't in the file yet.
    appended_header = False
    for key, value in updates.items():
        if key in seen or value == "":
            continue
        if not appended_header:
            if new_lines and new_lines[-1].strip() != "":
                new_lines.append("")
            new_lines.append("# Added via Settings UI")
            appended_header = True
        new_lines.append(f"{key}={_quote_if_needed(value)}")

    contents = "\n".join(new_lines).rstrip() + "\n"

    # Atomic replace so a crash mid-write can't leave a half-broken .env.
    fd, tmp_path = tempfile.mkstemp(prefix=".env.", dir=str(p.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(contents)
        os.replace(tmp_path, p)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    # Reflect the change in the running process so downstream callers (LLM
    # factory, source clients) see the fresh key without a server restart.
    for key, value in updates.items():
        if value == "":
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

    # Drop the cached `Settings` so the next get_settings() rebuilds from env.
    get_settings.cache_clear()  # type: ignore[attr-defined]
    # Same for the LLM cache, since the active provider/model may have changed.
    try:
        from .llm.factory import get_llm

        get_llm.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        pass

    return read_env_file(p)


def _quote_if_needed(value: str) -> str:
    """Wrap values containing whitespace or quotes so they round-trip cleanly."""
    if value == "":
        return ""
    needs_quote = any(c.isspace() for c in value) or any(c in value for c in '"\'#')
    if not needs_quote:
        return value
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'
