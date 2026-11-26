"""Investor target loading for the Vektor Outreach Agent."""

import json
from pathlib import Path

DEFAULT_TARGETS_PATH = Path(__file__).resolve().parent.parent / "targets.json"


class TargetError(RuntimeError):
    pass


def load_targets(path=None):
    path = Path(path) if path else DEFAULT_TARGETS_PATH
    if not path.exists():
        raise TargetError("targets file not found: %s" % path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        raise TargetError("targets file is not valid JSON: %s" % path) from None
    targets = data.get("targets")
    if not isinstance(targets, list):
        raise TargetError("targets file must contain a top-level 'targets' list.")
    return targets


def find_target(targets, name):
    """Exact (case-insensitive) match first, then unique substring match."""
    wanted = name.strip().lower()
    for target in targets:
        if target.get("name", "").lower() == wanted:
            return target
    matches = [t for t in targets if wanted in t.get("name", "").lower()]
    if len(matches) == 1:
        return matches[0]
    names = ", ".join(sorted(t.get("name", "?") for t in targets))
    if not matches:
        raise TargetError("No target named %r. Known targets: %s" % (name, names))
    raise TargetError(
        "Name %r matches more than one target (%s). Use the full name."
        % (name, ", ".join(t.get("name", "?") for t in matches))
    )
