# Load tests (k6)

Latency/throughput checks from `docs/test-plan.md` §10. Require a running, seeded stack.

```bash
# Steady load — API responsiveness (PERF-06) + health
k6 run -e BASE_URL=http://localhost:8000 \
       -e EMAIL=reviewer@sanad.local -e PASSWORD=sanad-dev-password \
       infra/load/api_load.js

# Spike — graceful degradation (PERF-05)
k6 run -e BASE_URL=http://localhost:8000 infra/load/spike.js
```

Thresholds fail the run (non-zero exit) when breached, so these gate in CI on a
performance runner. The heavy pipeline SLOs (50-page contract ≤ 10 min, Idea Check
≤ 5 min — PERF-01/02) are measured separately by timing the async jobs end to end, not
by k6, which targets the synchronous API surface.
