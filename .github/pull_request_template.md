## Summary

<!-- One or two lines: what this PR does and why. -->

## Changes

<!-- Bullet the concrete changes. Note any schema/API change and the doc updated in the
     same PR (database.md / api-contracts.md / architecture.md). -->

-

## Test plan

<!-- How you verified. Reference test IDs from docs/test-plan.md where relevant. -->

- [ ] Invariant tests pass (citation gate, append-only, reviewed-only scoring, audit)
- [ ] `docker compose run --rm api pytest` green (if backend touched)
- [ ] `npm run typecheck` + `npm run build` (if frontend touched)
- [ ] Sandbox isolation tests pass/skip appropriately (if sandboxes touched)
- [ ] Arabic + English paths verified (if UI touched)

## Invariant checklist (AGENTS.md)

- [ ] No finding path without a resolvable citation
- [ ] Append-only tables untouched by UPDATE/DELETE
- [ ] Untrusted input wrapped before any LLM call; no provider SDK outside `services/llm`
- [ ] New state changes write to `audit_log`; no secrets in code/config/logs
