# ddg-xgrok-mirror

An MIT-licensed Hermes skill for X account management: discover reply targets,
draft three alternatives with an LLM, queue them, select one as a human, and
publish only that approved reply. The **Grok-mirror** concept is a local,
inspectable alternative workflow, not an xAI integration or a claim of feature
parity with a first-party bot. Public release is pending owner approval.

## Why open-source it

Account operators should be able to inspect the boundary between a model's
suggestion and a write to their account. This repository exposes the approval
checks, queue format, voice-calibration contract, and tactics playbook rather
than hiding them in a managed bot. It supports model selection through Hermes;
it does not require Grok or X API credits for the existing browser adapter.
That adapter is not automatically permitted by X policy; see limitations below.

## Architecture

```text
X discovery / authorized target JSON       account voice + persona remit
                 |                                      |
                 v                                      v
          scan / rank ---------------------------> LLM draft
                                                     |
                                              strict JSON checks
                                                     |
                                         queue (draft, failed=true)
                                                     |
                                            human select/approve
                                                     |
                                       HMAC-bound selected reply
                                                     |
                                         post + expected-handle guard
                                                     |
                                      backend result queue readback
                                                     |
                                posted URL OR fenced manual reconciliation

compose --> original-post alternatives --> human review/export only
mentions / thread / feedback --> bounded read-only snapshots
```

`xgrok` coordinates account-local state and advisory locks. `xgrok_draft.py`
loads the account's voice guide and calls `hermes chat`. `xgrok_compose.py`
drafts original posts but has no original-post publishing adapter.
`xgrok_observe.py` reads mentions, parent chains and feedback through the
existing browser backend. References explain tactics to keep or reject and
how account-specific voice is sourced; their examples are not proven metrics.

## Quickstart

Requires Python 3.10+ on Linux/macOS and a configured Hermes installation.
After the owner publishes the reviewed repository, install the skill (replace
`OWNER` with the approved GitHub owner; no repository is assumed live yet):

```bash
hermes skills install OWNER/ddg-xgrok-mirror --category social-media
```

This is an extracted integration, **not a standalone X client**. The current
code expects support modules at `~/hermes/x-growth-support/scripts/`
(`discover_reply_targets.py` and `rank_reply_targets.py`) and the existing
browser environment `~/x-deleter/.venv/bin/python` plus
`~/x-deleter/scripts/x_rebrand_ddg.py`. Those components, browser profiles,
credentials, live queues and account voice guides are not bundled. Do not
assume installing the skill provisions them. Without those adapters, use
supplied target JSON for draft/review and do not run browser commands.

Configure your own account directory under
`~/hermes/x-growth-support/accounts/YOUR_HANDLE/` with `account_config.json`:

```json
{"handle":"YOUR_HANDLE","expected_handle":"YOUR_HANDLE","browser_profile":"/absolute/path/to/your/authorized/profile"}
```

Add `VOICE_GUIDE.md` with your register, factual-review rules and approved links.
Optional `xgrok.json` must contain all remit fields:

```json
{"persona":"Technical builder","topics":["agent infrastructure"],"banned_tactics":["hashtags","engagement bait"],"voice_path":"VOICE_GUIDE.md","max_replies_per_day":5,"require_approval":true}
```

From the installed skill directory, the reply workflow is:

```bash
python3 scripts/xgrok --help
python3 scripts/xgrok scan --handle YOUR_HANDLE
python3 scripts/xgrok draft --handle YOUR_HANDLE --limit 3 --queue
python3 scripts/xgrok status --handle YOUR_HANDLE
python3 scripts/xgrok approve --handle YOUR_HANDLE
# Separate explicit publishing action: only if X authorization/policy permits.
python3 scripts/xgrok post --handle YOUR_HANDLE --id APPROVED_REPLY_ID --expected-handle YOUR_HANDLE
```

For supplied targets, skip scan and use
`draft --handle YOUR_HANDLE --input /absolute/path/to/targets.json --queue`.
The input accepts a list or a `top_unreplied` array; each target needs `url`,
`text`, `author` and string `status_id` matching its canonical X URL.
Use `compose --handle YOUR_HANDLE` for original-post alternatives only, with
`content_pillars` or `content_mix_contract` in the account configuration.
Publishing original posts is manual; `approve` and `post` above handle replies.
Do not run live scan/post commands as installation tests.

Offline checks (model and publishing subprocesses mocked):

```bash
python3 scripts/test_xgrok.py
python3 scripts/test_xgrok_compose.py
python3 -m py_compile scripts/xgrok scripts/xgrok_draft.py scripts/xgrok_compose.py scripts/xgrok_observe.py
```

## Honest limitations and trust boundaries

- **Approval is local single-owner trust.** HMAC binds item identity, option,
  target, text and timestamp to a mode-0600 local key. It does not prove human
  intent against the same OS owner or root, who can read the key or run approve.
  It is not hostile-tenant isolation; history and quotas are locally mutable.
- **The drafting model is an agent runtime.** `--oneshot --max-turns 1` is not
  a sandbox or a guarantee that a tool-enabled model cannot act. Use a trusted,
  tool-restricted configuration; treat source posts and voice files as untrusted.
- **Review remains necessary.** Reply validation uses Python character counts,
  not complete X weighted length. Compose has URL/Unicode weighting but not a
  complete emoji grapheme parser. Truth, voice, canonical ownership, bare-domain
  links and source interpretation require human checks.
- **No autonomous original-post publishing.** Compose does not hand off to live
  queues. Legacy approve-all scripts are unsafe substitutes for per-item approval.
- **Legacy workers must be paused/upgraded.** `failed=true` fences prevent unsafe
  legacy consumption; do not clear them. Advisory locks coordinate only cooperating
  xgrok writers. Do not delete lock files or automatically retry uncertain posts.
- **Readback scope is limited.** Posting trusts the backend's isolated result
  queue; xgrok does not independently reread X to prove publication. Reconcile
  missing URLs or uncertain results manually. Observation snapshots are bounded.
- **X automation policy applies.** Human approval alone does not establish
  compliance. Review https://help.x.com/en/rules-and-policies/x-automation;
  non-API website scripting and AI replies have policy restrictions, including
  prior written explicit X approval for AI reply bots. Default to authorized
  inputs, drafting, human review/export and manual publication. Only enable the
  browser publishing adapter with separate authorization and policy permission.
- **Trademark.** Grok is xAI's trademark; X belongs to its respective owner.
  “Grok-mirror” describes the concept only. This project is not affiliated with,
  endorsed by, or an official integration of xAI or X. MIT covers our code,
  not third-party trademarks, account access or platform permissions.

The copied references retain founder-account examples and local paths. They
are not @DaedalusAgents' brand voice. In `references/voice-calibration.md`, the
older assertion that one-shot mode prevents tool actions is not a security
promise; the runtime caveat above and in SKILL.md controls. Its older URL-check
summary is also stale: the current validator requires recognized URLs to match
source URLs exactly, but still does not establish canonical ownership.

## Commercial context

[DDG's catalog](https://agents.daedalusdevelopmentgroup.com/ai.txt),
[llms.txt](https://agents.daedalusdevelopmentgroup.com/llms.txt), and
[hosted MCP transport](https://mcp.daedalusdevelopmentgroup.com/mcp) are the
commercial edge this skill's approval pipeline grew out of. These are separate
agent-payable services, not a requirement or subscription for this MIT skill.
The MCP hostname root may return 404; use `/mcp` for the protocol transport.
Signed provenance establishes origin and integrity, not factual correctness.

See [SKILL.md](SKILL.md) for full commands, queue fences and residual risks,
[CONTRIBUTING.md](CONTRIBUTING.md) for changes, and
[PREPARE_PUSH.md](PREPARE_PUSH.md) for owner-only publication steps.
