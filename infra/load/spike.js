// k6 spike test (test-plan §10 PERF-05): a burst of traffic must degrade gracefully, not
// drop requests. Run: k6 run -e BASE_URL=http://localhost:8000 infra/load/spike.js
import http from "k6/http";
import { check } from "k6";

const BASE = (__ENV.BASE_URL || "http://localhost:8000") + "/api/v1";

export const options = {
  scenarios: {
    spike: { executor: "ramping-vus", startVUs: 0,
      stages: [
        { duration: "10s", target: 5 },
        { duration: "10s", target: 100 }, // sudden spike
        { duration: "30s", target: 100 },
        { duration: "10s", target: 0 },
      ],
    },
  },
  thresholds: {
    // Under spike, health must stay available and errors bounded (graceful degradation).
    "http_req_failed": ["rate<0.05"],
    "http_req_duration": ["p(95)<2000"],
  },
};

export default function () {
  const res = http.get(`${BASE}/health`);
  check(res, { "health reachable": (r) => r.status === 200 });
}
