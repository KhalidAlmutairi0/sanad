# Contributing to SANAD

## Branch + PR workflow

`main` is the protected line by convention — do not commit to it directly. All changes go
through a pull request.

1. Branch from `main`: `git checkout main && git pull && git checkout -b <type>/<short-topic>`
   (`type` ∈ `feat`, `fix`, `chore`, `docs`, `test`, `refactor`).
2. Make small, focused commits. If you change schema, an API contract, or a data flow,
   update the relevant doc (`docs/database.md` / `docs/api-contracts.md` /
   `docs/architecture.md`) in the SAME commit.
3. Run the relevant checks before opening the PR (see the PR template's test plan).
4. Open a PR into `main`. CI runs automatically; keep it green. Self-merge is allowed once
   CI passes (solo repo), but never bypass the invariant tests.

## Non-negotiables

`AGENTS.md` holds the hard invariants; a PR that weakens one is rejected. The full test
methodology and coverage matrix live in `docs/test-plan.md`.

## Note on enforcement

This repo is private on a plan without server-side branch protection, so the rules above
are enforced by convention (and by CI visibility on each PR), not by GitHub blocking pushes
to `main`. If the repo moves to a plan/visibility that supports it, apply the `protect-main`
ruleset: require a PR + passing `Static invariants` and `Frontend typecheck + build`
checks, and block force-push and deletion on `main`.
