<!-- SPDX-License-Identifier: MIT -->
# Tactics playbook: @0xcircuitbreakr

This is a founder/developer build log, not a promotional feed. Borrow conversational mechanisms, not another account's language. The account voice guide overrides engagement tactics.

## Evidence and objective

An earlier supplied analysis (not independently re-verified by this skill) of @unvibeapp (32 followers) reports 71–164 likes on #connect posts versus 1–5 on product posts. That is an observation, not evidence that hashtags cause engagement or that these results transfer. DDG's @DaedalusAgents already receives 86–191 likes but approximately zero replies/reposts: the gap is conversation, not reach. Those figures describe the source accounts, not @0xcircuitbreakr.

Optimize for substantive technical replies and continued exchanges, not likes alone. Examples below are draft patterns, not assertions that work has shipped; confirm every project claim before use.

## Keep / adapt / remove

| Tactic | Decision | Why | Adaptation for x402 / agent infrastructure |
| --- | --- | --- | --- |
| 1. #connect posts / “drop what you're building” reply-bait | **ADAPT** | Keep peer discovery, remove hashtags and generic engagement bait. | Share a concrete integration constraint, then invite relevant implementation evidence: `comparing x402 retry handling at the settlement boundary. interested in traces where the receipt arrived after the client timed out.` |
| 2. Questions as endings | **ADAPT** | Genuine, bounded engineering questions can start useful exchanges; rhetorical questions violate the voice guide. | `for x402 retries, does your idempotency key identify the tool call or the payment attempt?` Use only when this is an actual unresolved question; do not append a question mechanically. |
| 3. Original-data authority posts | **KEEP** | Reproducible measurements supply useful evidence without slogans. | After a real audit, replace every placeholder: `checked [n] agent payment integrations at [commit/date]. [k] replayed a paid request after timeout. method: [canonical artifact].` Never reuse the source's “24 apps / 67%” as our data. |
| 4. Relatable GIF/meme posts | **REMOVE** | Reaction media and generic relatability displace the account's artifact-first engineering register. | Use a redacted trace or minimal failing test instead: `payment settled; tool response timed out. the retry boundary is the part worth testing.` Only publish with evidence that this happened. |
| 5. Quote-tweets of large accounts with hot takes | **ADAPT** | A mechanism-level correction is useful; audience size and provocation are not sufficient reasons to quote. | Quote a relevant payment-design claim and add a bounded distinction: `settlement and tool execution are separate outcomes. a payment receipt alone does not establish that the tool returned a result.` No gratuitous @-mentions. |
| 6. Shoutouts / freebies | **ADAPT** | Offer a useful artifact or credit a verified contribution, not reciprocal promotion or giveaways. | Publish an actual owned test fixture for duplicate paid requests; explain its assertions and limits. Credit contributors only with approved mentions; no third-party repository promotion. |
| 7. Product launches with link footer | **ADAPT** | Keep concrete release notes and canonical destinations, remove sales language and unsupported shipping claims. | After a public tag exists: `[project] [version] is released. [verified behavior and limitation]. [canonical owned link]` Otherwise use `under review`, `building`, or another evidenced state. |
| 8. Contrarian one-line monetization takes | **ADAPT** | Replace aphorisms with a specific payment tradeoff that can be discussed or tested. | `a spend cap checked after settlement cannot prevent that settlement from exceeding the cap.` Add the actual preflight mechanism or limitation when available; avoid universal claims about agent economics. |
| 9. Bursty cadence | **REMOVE** | Posting in bursts makes conversation follow-through harder and confounds comparisons between tactics. | Use a sustainable cadence with time reserved for technical replies; publish an x402 build note when evidence exists, not to fill a burst quota. |

## Operating constraints

- Lowercase, terse, engineer-to-engineer; no hashtags, emoji, exclamation marks, slogans, or rhetorical questions.
- Prioritize opentine, agent infrastructure / x402, then other documented account pillars. Do not impersonate the @DaedalusAgents brand account.
- Replies name the target's mechanism and add a constraint, number, or failure mode. A genuine question must be specific enough for an engineer to answer.
- Links are sparse (roughly one post in four), owned and canonical, and a payoff rather than a substitute for useful text. Do not add third-party repo links. Ground project claims in canonical evidence even when a post omits a URL.
- Require human approval before publishing or mentioning anyone. Verify the active account before any X write.
- Compare substantive replies, unique technical participants, follow-up exchanges, and reposts over comparable observation windows. Retain likes as context; do not invent improvement targets or infer causality from a small sample.
