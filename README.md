# Vektor Outreach Agent

Drafts investor outreach (emails and posts) for **VektorFlow AI Systems**.
Wallace approves every draft before anything could ever go out.

**V1 has no sending capability at all.** It produces drafts and keeps an
approval queue. There is no send command, no email code, no posting code.
Approving a draft only changes its header status from `DRAFT — NOT SENT`
to `APPROVED`. Nothing leaves this machine.

## How it works

- **Brain:** Meta Model API (`POST https://api.meta.ai/v1/chat/completions`,
  OpenAI-compatible), called with the Python standard library only
  (`urllib`). No pip dependencies.
- **Targets:** `targets.json` in this directory — 11 investors seeded from
  the Nov 25, 2026 research file
  (`~/workspace/goals/founder-story-and-pitch/files/investor-targets.md`).
  Only contact routes documented in that research are listed; where none
  was found, `contact_route` is `null`. No email was invented.
- **Drafting:** the brain is prompted with a fixed fact set (founder in
  Hampton SC; Vektor Agent — owner's machine, owner's keys, approval-gated,
  sanitized logs; independently verified 10/10 tests, 119 checks; built on
  free tools; priced for sale, no figure). No traction numbers, no invented
  claims. Drafts land in `drafts/` as markdown with a header
  (`target`, `date`, `status: DRAFT — NOT SENT`).
- **Approval gate:** a draft's status can only change through the
  `approve` command.

## Setup

Set the Meta Model API key in the environment **where the agent runs**
(never hardcode it, never put it in chat):

```bash
export META_MODEL_API_KEY="<your key from dev.meta.ai>"
# optional: pick a different model (default: muse-spark)
export META_MODEL="muse-spark"
```

If `META_MODEL_API_KEY` is missing, the agent prints a clear error and
makes **no** API call.

## Commands

```bash
python -m outreach draft --target "EPIC Ventures"   # draft an email
python -m outreach list                             # show drafts + statuses
python -m outreach approve drafts/epic-ventures-2026-11-25.md
```

## Tests

```bash
python -m unittest discover -s tests -v
```

## Honest note: where the brain can run

`api.meta.ai` must be reachable from the machine running this agent.
The build VM **cannot** reach it (verified: the VM's proxy returns 403
for api.meta.ai), so the live brain test cannot happen there. Run the
agent on Wallace's phone (Termux) or on Render — with his
`META_MODEL_API_KEY` set in that environment — to test the brain live.
Until that test passes, the Meta brain is **wired but unverified**.
