"""Opt-in .env loader for the paper_search scripts.

Why: the source connectors read credentials via os.environ (e.g. OPENREVIEW_USER/PASS).
When these scripts are invoked directly by an LLM through bash, the shell has NOT sourced
any .env, so those vars are empty and the credentialed sources silently degrade. With
explicit project opt-in, this module walks up from the script directory and loads only
connector keys from an allowlist — shell-set vars take precedence.

Search order (first match wins):
  1. .env in any ancestor directory of this script (scripts/ -> paper_search/ -> skills/ -> repo root)
  2. any skills/<name>/.env under the repo root (keys currently live in skills/ResearchStudio-Idea/.env)
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

_loaded = False

_ALLOWED_KEYS = {
    "OPENREVIEW_USER",
    "OPENREVIEW_PASS",
    "OPENALEX_MAILTO",
    "OPENALEX_API_KEY",
    "SEMANTICSCHOLAR_API_KEY",
}


def _apply(env_path: Path) -> None:
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key in _ALLOWED_KEYS:
            # setdefault: a value already exported in the real shell wins over the .env file.
            os.environ.setdefault(key, val)


def load_env_once() -> Optional[Path]:
    """Load the first .env only after explicit opt-in; otherwise do nothing."""
    global _loaded
    if _loaded:
        return None
    _loaded = True

    if os.environ.get("RESEARCHSTUDIO_LOAD_DOTENV") != "1":
        return None

    here = Path(__file__).resolve()
    candidates: list[Path] = []
    repo_root: Optional[Path] = None
    for parent in here.parents:
        candidates.append(parent / ".env")
        if (parent / ".git").exists():
            repo_root = parent
            break
    if repo_root is not None:
        candidates += sorted(repo_root.glob("skills/*/.env"))

    for cand in candidates:
        try:
            if cand.is_file():
                _apply(cand)
                return cand
        except OSError:
            continue
    return None
