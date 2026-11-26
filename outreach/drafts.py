"""Draft storage and the approval gate.

Drafts are markdown files in drafts/ with a small header:

    ---
    target: EPIC Ventures
    date: 2026-11-25
    status: DRAFT — NOT SENT
    ---

The ONLY way a draft's status changes is the approve command in this
module. There is no send capability anywhere in v1.
"""

import re
from datetime import date
from pathlib import Path

DEFAULT_DRAFTS_DIR = Path(__file__).resolve().parent.parent / "drafts"

STATUS_DRAFT = "DRAFT — NOT SENT"
STATUS_APPROVED = "APPROVED"

_HEADER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
_STATUS_LINE_RE = re.compile(r"^status:\s*(.+)$", re.MULTILINE)


class DraftError(RuntimeError):
    pass


def _slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def build_prompt(target):
    """The drafting prompt. Only the facts Wallace approved may be used."""
    return (
        "Write a short investor outreach email from Wallace Thomas, founder "
        "of VektorFlow AI Systems, to %s (%s stage investor).\n\n"
        "Use ONLY these facts — invent nothing else:\n"
        "- Wallace is a founder based in Hampton, South Carolina.\n"
        "- He built Vektor Agent, a privacy-respecting AI agent: it runs on "
        "the owner's machine with the owner's own API keys, every risky "
        "action is approval-gated by the owner, and its logs are sanitized "
        "so secrets are redacted.\n"
        "- Vektor Agent was independently verified: 10/10 verification "
        "tests passed, 119 checks.\n"
        "- It was built entirely on free tools.\n"
        "- It is priced for sale (do not state any price or figure).\n\n"
        "Rules: plain, direct voice — like a real person talking, not "
        "corporate copy. No traction numbers, no revenue claims, no user "
        "counts, no invented claims of any kind. Keep it under 180 words. "
        "End by asking for a short call. Output only the email text, "
        "starting with a subject line."
        % (target.get("name", "the investor"), target.get("stage", "early"))
    )


def write_draft(target, email_text, drafts_dir=None, today=None):
    drafts_dir = Path(drafts_dir) if drafts_dir else DEFAULT_DRAFTS_DIR
    drafts_dir.mkdir(parents=True, exist_ok=True)
    day = (today or date.today()).isoformat()
    path = drafts_dir / ("%s-%s.md" % (_slug(target.get("name", "target")), day))
    counter = 2
    while path.exists():
        path = drafts_dir / (
            "%s-%s-%d.md" % (_slug(target.get("name", "target")), day, counter)
        )
        counter += 1
    header = "---\ntarget: %s\ndate: %s\nstatus: %s\n---\n\n" % (
        target.get("name", ""),
        day,
        STATUS_DRAFT,
    )
    path.write_text(header + email_text.strip() + "\n", encoding="utf-8")
    return path


def read_header(path):
    text = Path(path).read_text(encoding="utf-8")
    match = _HEADER_RE.match(text)
    if not match:
        raise DraftError("No header found in %s — not a draft file." % path)
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def approve_draft(path):
    """Flip a draft's status to APPROVED. This is the only status change.

    Approving sends nothing — v1 has no send capability at all.
    """
    path = Path(path)
    if not path.exists():
        raise DraftError("Draft file not found: %s" % path)
    text = path.read_text(encoding="utf-8")
    header_match = _HEADER_RE.match(text)
    if not header_match:
        raise DraftError("No header found in %s — not a draft file." % path)
    header = header_match.group(1)
    status_match = _STATUS_LINE_RE.search(header)
    if not status_match:
        raise DraftError("No status line in the header of %s." % path)
    if status_match.group(1).strip() == STATUS_APPROVED:
        return path  # already approved; nothing changes
    new_header = _STATUS_LINE_RE.sub("status: " + STATUS_APPROVED, header, count=1)
    new_text = "---\n" + new_header + "\n---\n" + text[header_match.end():]
    path.write_text(new_text, encoding="utf-8")
    return path


def list_drafts(drafts_dir=None):
    drafts_dir = Path(drafts_dir) if drafts_dir else DEFAULT_DRAFTS_DIR
    if not drafts_dir.exists():
        return []
    rows = []
    for path in sorted(drafts_dir.glob("*.md")):
        try:
            fields = read_header(path)
        except DraftError:
            continue
        rows.append(
            {
                "file": path.name,
                "target": fields.get("target", "?"),
                "date": fields.get("date", "?"),
                "status": fields.get("status", "?"),
            }
        )
    return rows
