// k6 API load test (test-plan §10: PERF-06 list latency, health).
// Run against a running, seeded stack:
//   k6 run -e BASE_URL=http://localhost:8000 -e EMAIL=reviewer@sanad.local \
//          -e PASSWORD=sanad-dev-password infra/load/api_load.js
import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const BASE = (__ENV.BASE_URL || "http://localhost:8000") + "/api/v1";
const EMAIL = __ENV.EMAIL || "reviewer@sanad.local";
const PASSWORD = __ENV.PASSWORD || "sanad-dev-password";

const errors = new Rate("app_errors");
const listLatency = new Trend("contracts_list_ms", true);

export const options = {
  scenarios: {
    steady: { executor: "ramping-vus", startVUs: 0,
      stages: [
        { duration: "30s", target: 20 },
        { duration: "1m", target: 20 },
        { duration: "20s", target: 0 },
      ],
    },
  },
  thresholds: {
    // PERF-06: list endpoints stay responsive under load.
    "contracts_list_ms": ["p(95)<800"],
    "http_req_duration{endpoint:health}": ["p(95)<200"],
    "app_errors": ["rate<0.01"],
  },
};

export function setup() {
  const res = http.post(`${BASE}/auth/login`, JSON.stringify({ email: EMAIL, password: PASSWORD }), {
    headers: { "Content-Type": "application/json" },
  });
  check(res, { "login ok": (r) => r.status === 200 });
  return { token: res.status === 200 ? res.json("token") : null };
}

export default function (data) {
  const health = http.get(`${BASE}/health`, { tags: { endpoint: "health" } });
  check(health, { "health 200": (r) => r.status === 200 }) || errors.add(1);

  if (data.token) {
    const auth = { headers: { Authorization: `Bearer ${data.token}` }, tags: { endpoint: "contracts" } };
    const list = http.get(`${BASE}/contracts?limit=25`, auth);
    listLatency.add(list.timings.duration);
    check(list, { "contracts 200": (r) => r.status === 200 }) || errors.add(1);
  }
  sleep(1);
}
