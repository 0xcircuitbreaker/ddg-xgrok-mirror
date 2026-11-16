# Contributing

Open an issue describing the behavior and safety boundary before a large change.
Keep model-generated drafts separate from approval and publication. Do not add
implicit publishing, clear legacy fences, bypass account identity checks, or
weaken HMAC verification. Preserve MIT/SPDX notices.

Run both offline suites and compile the entrypoints listed in README.md.
Add mocked fail-closed tests for any queue, identity, retry or approval change.
Never use real accounts or publish to test a gate. Do not include profiles,
credentials, approval keys, account queues, private voice guides or raw analytics.

Document external adapter requirements and distinguish implemented guarantees
from human-review responsibilities. Report vulnerabilities privately to the
maintainer via the approved contact rather than including sensitive queues or
keys in a public issue. This packet does not establish a response-time SLA.
