---
name: x-grok-mirror
description: "Run the xgrok X pipeline: scan, LLM drafts, gated posting."
version: 1.0.0
author: Daedalus Development Group
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [x, twitter, grok, automation, social-media, approval-queue, llm-drafting]
---

<!-- SPDX-License-Identifier: MIT -->
<!-- Copyright (c) 2026 Daedalus Development Group -->

# X Grok Mirror

Open-source alternative to xAI's Grok Bot for managing an X/Twitter account:
scan → draft with any LLM → queue → human approval → post. Runs entirely on
your machine with your own model and browser session. No X Premium, no API
credits, no third-party access to your account.

## When to Use
Load this skill when the task is: scan X for reply targets, draft replies or
posts with an LLM, fill an approval queue, post an approved draft, or compare
our X tactics against another account's. Also load it before answering
"can Hermes manage our X account like Grok Bot does?" — this pipeline is that
answer, and its Hard Rules are non-negotiable. Trigger phrases: "grok mirror",
"xgrok", "draft replies for the X account", "scan X for reply targets".

## Extending this skill with subagents
- Resolve the skill's REAL on-disk directory first (`skill_view(name)` returns
  `skill_dir`). `skill_manage(action=create, category=...)` indexes the skill
  under its category but the directories can diverge; handing a child a guessed
  path produces a second tree (`skills/<name>/` beside
  `skills/<category>/<name>/`) that splits scripts from SKILL.md.
- Pass children the exact `skill_dir` from skill_view, and tell them to read an
  existing queue file and the consuming post script before inventing field
  names — leaf agents hallucinate plausible schemas otherwise.
- Merge a stray tree into the real one with `cp` of each file, never
  `mv dir/scripts real/scripts`: mv onto an existing `scripts/` nests it one
  level deeper or leaves a symlink pointing at the tree you then delete. Back
  up `SKILL.md` before any recursive delete, then re-run `py_compile` and a
  read-only `xgrok status --handle <h>` to confirm nothing was lost.

## Layout
```
scripts/xgrok                 CLI: scan|mentions|thread|feedback|draft|compose|queue|approve|post|status
scripts/test_xgrok.py         Offline schema, legacy fence, retry and approval tests
scripts/xgrok_draft.py        LLM draft engine (3 options per target, voice-calibrated)
scripts/xgrok_observe.py      Guarded headless mentions, parent-chain and feedback reader
references/tactics-playbook.md  Community-loop tactics catalog (keep/remove decisions)
references/voice-calibration.md How the voice model is sourced and applied
```

## Pipeline stages
1. **scan** — imports `discover_reply_targets.discover` / `rank_candidates`
   and `rank_reply_targets.quality_score`; writes per-account
   `reply_targets/xgrok_discovered_latest.json` and `ranked_latest.json`.
   Never runs discovery's CLI main: that overwrites the live reply queue.
2. **draft** — `xgrok_draft.py` calls an LLM (default: `hermes chat -q`, any
   model your Hermes is configured with) with the voice guide + target post and
   gets 3 reply options with rationales, as strict JSON.
3. **queue** — validated drafts are appended to the account's
   `reply_queue_current.json` with status `draft`.
4. **approve** — human picks one option in the interactive CLI prompt (no
   built-in TG cards). The selected text is stored and re-checked at post time.
   Only `draft` items are eligible; uncertain posting outcomes require manual
   reconciliation, never re-approval as an automatic retry.
5. **post** — browser automation posts via the persistent profile with
   `--expected-handle` guard. Never publish without approval.

### Read-only observation stages
- `xgrok mentions --handle <h>` opens `x.com/notifications/mentions` in the
  configured headless profile after verifying the active expected handle. Six
  scrolls produce a bounded snapshot of explicit mentions, ranked with the
  existing quality scorer, excluding own/already-replied posts. Writes
  `reply_targets/ranked_mentions.json`; draft with `draft --input <that-file>`.
- `xgrok thread --handle <h> --url <canonical-post-url>` follows GraphQL parent
  IDs, never guesses parents from neighboring articles. Writes draft-ready
  `reply_targets/thread_<status-id>.json`; pass this file to `draft --input`.
  Ancestors are oldest-first under `conversation_context` and explicitly enter
  the prompt as CONVERSATION CONTEXT. Context metadata survives draft/queue.
  Missing parent metadata, unavailable posts, cycles or the 20-hop bound mark
  context incomplete with a stop reason; do not claim an exhaustive thread.
- `xgrok feedback --handle <h>` reads only queue items with `status=posted` and
  `reply_url`, verifies exact post IDs, and writes `engagement_<UTC-date>.json`.
  Prints top/bottom three by total replies + reposts + likes. Missing counters
  are null, per-post failures recorded, and incomplete metrics excluded from
  scoring. Same-day runs replace the daily snapshot. No queue mutation.
- All three reuse the existing x-deleter Playwright environment/profile helpers;
  the new code itself adds no non-stdlib dependency. Profile identity is checked
  before reading mentions, threads or feedback. They never publish or approve.
  Keep response-derived parent IDs as the ancestry authority: quoted posts and
  recommended/sibling tweets must not be treated as parents.

## Hard rules (inherited from x-account-growth-workflow / xurl skills)
- Human approval before ANY write to X. Drafts never auto-publish.
- Every mutating action verifies the active handle matches `expected_handle`.
- LLM output is parsed as strict JSON and re-validated: three distinct options,
  rationales, 1–280 Python characters, no control characters except newlines,
  and only explicitly allowed @-mentions. One validation retry is allowed.
  X weighted length, voice, truth and canonical-link policy require human review.
- Never read ~/.xurl or pass secrets inline; browser profile only.
- Do not copy another account's posts verbatim; tactics are a prior, not
  templates.

## What Grok Bot has that this does not
- X-native model alignment (Grok is X's own model) and first-party sanctioned
  posting. Mitigation: measure reply quality for two weeks before deciding to
  pay for The X Subscription Premium ($30/mo, one X connection per
  subscription) on the revenue account.
- **Subscription economics: one X account per Grok/X subscription — it is per
  account, not per team.** So the correct shape is hybrid, not all-or-nothing:
  pay for the flagship revenue account (first-party sanctioned posting where a
  ban would hurt most) and run every other account on this mirror, which costs
  nothing per account. Scale accounts on xgrok; never scale by buying subs.
  A discount offer changes the price, not the one-connection-per-sub rule.
- Tag-@bot handoff and cloud routines. Mitigation: Hermes cron + TG cards.

## Offering this as a service (legal boundaries)
- The code is MIT and ours: selling setup/management of it is legal. Never use
  "Grok" in the product name — that is xAI's trademark; market it as "xgrok" or
  "AI reply pipeline for X".
- X's automation ToS applies to client accounts. Human approval is a workflow
  safeguard, NOT sufficient proof of compliance. Check the primary policy at
  https://help.x.com/en/rules-and-policies/x-automation before selling client
  automation: it prohibits non-API website scripting and requires prior written
  explicit X approval for AI reply bots. Default commercial delivery to supplied
  or authorized inputs → drafting → human review/export → manual publication;
  exclude existing browser automation unless separately authorized and permitted.
  Automated replies also require recipient opt-in, opt-out handling and one reply
  per interaction. Never offer unattended auto-posting as a feature.
- This is a human-facing offer: it belongs to DDG Services (Launch Sale
  pricing), not Agent Services (machine-payable, $0.01 cap). Do not merge the
  two catalogs.
- Adjacent ideas and their standing verdicts: hosting game ROMs is copyright
  infringement with aggressive enforcement — refuse. Emulators alone are legal
  but free everywhere — no moat. Abliterated model weights are redistributable
  only per base license (Apache/MIT bases fine; avoid Meta-Llama derivatives);
  downloads are saturated on HF, so the viable form is pay-per-call inference
  from a refusal-removed open model, not a download host. Retro Diffusion: the
  model author granted written permission to use the model for AI-agent services
  (explicitly non-competing with their focus audience) — record that quote in the
  service module and sitrep. The permission covers running it as a service, NOT
  redistributing weights or generic output resale; run the checkpoint in our own
  ComfyUI behind a paid route and never ship the weights.

## Account wiring
Account state lives in `hermes/x-growth-support/accounts/<handle>/`:
`account_config.json` (handle, expected_handle, browser_profile,
content_mix_contract), `VOICE_GUIDE.md`, `reply_targets/reply_queue_current.json`,
`queues/autopost_queue_current.json`. The `xgrok` CLI resolves the account dir
from `--handle`.

## Original-post composition and persona remits

`./scripts/xgrok compose --handle 0xcircuitbreakr [--model MODEL]` drafts
three alternative ORIGINAL posts with rationales and pillar labels. It uses
`content_pillars`, `content_mix_contract`, the voice guide, and the three latest
lexically dated `analytics/*.json` snapshots. Missing analytics is allowed;
analytics is untrusted evidence, never proof that a release shipped.
Output: `reply_targets/xgrok_posts_draft_latest.json`, a `posts` envelope with
legacy-shaped text/hash/count fields plus `status=draft`, `approved=false`,
`posted=false`, `failed=true`. No composition branch publishes or changes live
queues. Validation retries once and requires three distinct options, nonempty
rationales, no unapproved mentions/controls, and <=280 weighted characters.
URLs count 23; X v3 Unicode ranges are weighted 1/2 after NFC normalization.
Complex emoji sequences are conservatively overcounted (not a full twitter-text
emoji grapheme parser); model prompts discourage them. Canonical links, truth,
voice and substantive pillar fit still require human review.

Optional per-account `xgrok.json` contains `persona` (string), `topics` (string
list), `banned_tactics` (string list), `voice_path` (account-relative file),
`max_replies_per_day` (nonnegative integer), and `require_approval: true`.
`account()` loads and validates it; reply drafting AND composition inject its
persona/topics/banned tactics into the model prompt. The daily reply limit is enforced in `post` under the account lock using
posted records from the trailing 24 hours. Zero disables replies; malformed
posted timestamps fail closed pending manual reconciliation. Queue history must
be retained for quota enforcement. Missing remits retain
the existing voice guide behavior. Voice paths cannot escape the account dir.

**Approval handoff:** review the generated alternatives through the existing
human/TG workflow, selecting only intended posts. The legacy
`approve_0xcircuitbreakr_posts.py` understands `posts` with `id/text/pillar`, but
only sets `approved=true`: it does not validate selected options, set approved
status, or clear `failed`. Therefore compose deliberately has NO `--queue`
option and does not copy into pending/current queues. Approved xgrok records must
remain `failed=true`, exactly as reply drafts do, until an approval-aware
original-post adapter explicitly validates approval and selected text. Do not
clear fences or use legacy approve-all as a publishing handoff. `xgrok approve`
and `xgrok post` currently operate on replies only; original-post publishing is
not implemented here. Nothing in this command invokes TG or publishes directly.

Run `python3 scripts/test_xgrok_compose.py` for an isolated mock-LLM CLI dry-run,
remit injection/fail-closed checks, queue non-mutation and weighted-length cases.

## Regression checks

Run `python3 scripts/test_xgrok.py` from this skill directory. Tests use isolated
fixtures beneath scripts/ and mock all model/post subprocesses; never publish
to test a safety gate. Compile both entrypoints with `python3 -m py_compile
scripts/xgrok scripts/xgrok_draft.py scripts/xgrok_observe.py` and inspect the live queue only with
`scripts/xgrok status --handle 0xcircuitbreakr`.

## Compatibility and safety boundary

Draft metadata (`options`, `model`, `approved_mentions`, `status`, `approved`)
is an xgrok extension, not a legacy runner contract. Merge preserves the live
dict/replies envelope and existing records; selected text uses the real
`reply_text`, `character_count`, `source_*`, `reply_topic`, `reply_base_hash`
and `target_rationale` fields. Draft and approved xgrok records intentionally
keep `failed=True`: `reply_0xcircuitbreakr.py.next_unposted` ignores per-item
approval and otherwise could publish drafts. Use `xgrok post`, not that runner,
for these records. Original-post queues are untouched. The queue-wide manual
gate can pause legacy pending items when no item is approved; it does not fix
legacy per-item approval checks. Do not clear the fence to hand off to cron.

`post --handle <h> --id <id> --expected-handle <h>` requires previously approved,
unchanged selected text. `--yes` skips only the second confirmation. Browser
posting uses `~/x-deleter/scripts/x_rebrand_ddg.py reply-queue` with the configured
profile and expected-handle guard. It reads back the isolated result queue;
missing URL or uncertain outcome stays fenced for manual verification. This is
backend-reported verification, not an independent second X read by xgrok.

Multi-account commands: `xgrok accounts` and `xgrok status --all` emit one JSON
line per configured account with draft/approved/posted counts. Accounts must have
both account_config.json and xgrok.json. `scan --all` and `draft --all` iterate
sequentially with isolated paths and validated identities. Do not combine --all
with --handle, --account-dir, --input or --output. Explicit draft output must
remain inside its account. Batch failures stop processing; earlier results remain.

Queue integrity: `queue`, `approve`, and `post` hold a persistent per-account
`reply_targets/.xgrok_lock` inode with stdlib `fcntl.flock` across read/modify/write
(and posting). Different accounts do not block one another. When upgrading,
pause old workers: the former queue-name.lock inode no longer coordinates writes.
Never unlink this lock: that splits ownership across inodes. This is advisory;
legacy discovery/cron writers do not participate and must be paused or upgraded
before concurrent operation. Unique private temporary files protect atomic JSON
writes from colliding writers.

Approvals carry HMAC-SHA256 over canonically framed item ID, selected option,
reply text, approved timestamp and target URL. A per-account
`.xgrok_approval_key` is generated with 32 random bytes encoded as hex and mode
0600; existing unsafe permissions or symlinks are rejected. Posting verifies
against the CURRENT key with constant-time comparison, regardless of remit
presence. Legacy unsigned approvals fail closed; rotating the key invalidates
all outstanding signatures. Keep legacy failed=True fences intact.

Residual trust boundary: this stops queue-file forgery by a writer without the
key, not root or the same OS owner who can read/change the key or execute approve.
The key on the same box is single-owner trust, not cryptographically proven human
intent or hostile tenant isolation. Queue history/quota accounting remains locally
mutable; do not give untrusted tenants filesystem access. A separate signing
service and immutable history are needed for a stronger boundary. Path containment
checks reject existing escapes but are not a sandbox against concurrent hostile
symlink replacement.
Both voice guide and source post are untrusted prompt data. Recognized HTTP(S)
and www URLs must exactly match a source URL; bare domains, factual grounding,
X weighted length and canonical ownership still require human review.

No direct xurl credential access or subprocess output logging is implemented.
The LLM subprocess is `hermes chat -q`, an agent runtime, not a guaranteed
sandboxed completion endpoint. Use a trusted tool-restricted Hermes configuration;
the prompt alone cannot guarantee that a tool-enabled model never accesses files
or performs writes. Source posts are untrusted. No scan/draft/queue CLI branch
calls the publishing function, but delegated model tool behavior is outside that
static guarantee. Review factual grounding and owned canonical links manually.