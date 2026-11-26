"""Command-line interface for the Vektor Outreach Agent.

Commands:
    python -m outreach draft --target <name>   Draft an outreach email
    python -m outreach approve <draft-file>    Mark a draft APPROVED
    python -m outreach list                    Show drafts and statuses

V1 has no send command. Approving a draft only changes its header
status; nothing is ever transmitted by this program.
"""

import argparse
import sys

from . import brain, drafts, targets


def cmd_draft(args):
    all_targets = targets.load_targets(args.targets)
    target = targets.find_target(all_targets, args.target)
    prompt = drafts.build_prompt(target)
    email_text = brain.chat([{"role": "user", "content": prompt}])
    path = drafts.write_draft(target, email_text, drafts_dir=args.drafts_dir)
    print("Draft written: %s" % path)
    print("Status: %s. Review it, then run: python -m outreach approve %s"
          % (drafts.STATUS_DRAFT, path))
    return 0


def cmd_approve(args):
    path = drafts.approve_draft(args.draft_file)
    print("Approved: %s" % path)
    print("Note: approval only marks the draft. V1 cannot send anything.")
    return 0


def cmd_list(args):
    rows = drafts.list_drafts(drafts_dir=args.drafts_dir)
    if not rows:
        print("No drafts yet.")
        return 0
    for row in rows:
        print("%-40s %-28s %-12s %s"
              % (row["file"], row["target"], row["date"], row["status"]))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="outreach",
        description="Vektor Outreach Agent — drafts investor outreach. "
                    "Nothing sends without Wallace's approval; v1 cannot send at all.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_draft = sub.add_parser("draft", help="Draft an outreach email for a target")
    p_draft.add_argument("--target", required=True, help="Investor name from targets.json")
    p_draft.add_argument("--targets", default=None, help="Path to targets.json")
    p_draft.add_argument("--drafts-dir", default=None, help="Directory for draft files")
    p_draft.set_defaults(func=cmd_draft)

    p_approve = sub.add_parser("approve", help="Mark a draft APPROVED (sends nothing)")
    p_approve.add_argument("draft_file", help="Path to the draft .md file")
    p_approve.set_defaults(func=cmd_approve)

    p_list = sub.add_parser("list", help="List drafts and their statuses")
    p_list.add_argument("--drafts-dir", default=None, help="Directory for draft files")
    p_list.set_defaults(func=cmd_list)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (brain.MissingKeyError, brain.BrainError,
            drafts.DraftError, targets.TargetError) as error:
        print("error: %s" % error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
