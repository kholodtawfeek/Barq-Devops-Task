# Log analysis

## 1. Coverage, valid/malformed/duplicate lines

Time range covered: 2026-08-20T11:00:00.015Z to 2026-08-20T11:30:00.000Z (~30 minutes),
based on the earliest and latest parsed timestamps in access.log, plus a final
`[notice] log collector rotated stream` line in error.log at 11:30:00.

| File | Total lines | Valid JSON/format | Malformed | Duplicate request_ids |
|---|---|---|---|---|
| access.log | 726 | 725 | 1 (truncated JSON at 11:12:48Z) | 5 (lab-000121, 241, 361, 481, 601 - each appears twice) |
| application.log | 730 | 729 | 1 (truncated JSON at 11:17:00Z) | 0 |
| error.log | 68 | 67 (matches `YYYY/MM/DD HH:MM:SS [error]` format) | 1 (a `[notice]` log-rotation line, not an error) |

Commands used: iterated `json.loads()` over each line of each log file inside a try/except
block, printing any line that failed to parse; counted `request_id` occurrences with
`collections.Counter` to find duplicates.

## 2. Distinct client requests and de-duplication

725 valid access.log lines contain 5 duplicate `request_id` values. Each duplicate pair has
byte-identical fields (same timestamp, status, request_time) - confirmed by inspecting all
5 pairs directly. This is a log-write duplication artifact, not a retried request.
De-duplicating by `request_id` gives:

**720 distinct client requests.**

De-dup method: build a dict/set keyed by `request_id`, keep one record per key. Confirmed the
5 duplicate pairs are exact repeats (not two different outcomes for the same ID), so no
request was double-counted as both a failure and a success.

## 3. Final client status counts and error rate

After de-duplication (720 distinct requests):

| Status | Count |
|---|---|
| 200 | 615 |
| 503 | 47 |
| 502 | 40 |
| 404 | 10 |
| 504 | 8 |

**Error rate = 105 / 720 = 14.58%** (denominator = all distinct client-facing requests;
numerator = all non-200 responses).

## 4. Which paths, time windows, backends account for failures

- **502/504 (48 total)** - Incident 1, 11:05:02-11:09:57, upstream `172.23.0.12:8080` (app-02)
  only, across `/health`, `/ready`, `/records`, `/counter`, `/instance`, `/`.
- **503 (47)** split into two separate incidents:
  - 31 requests, 11:12:09-11:15:52, `/ready` and `/counter`, both app-01 and app-02 equally
    - Redis timeout.
  - 16 requests, 11:20:07-11:21:45, `/ready` and `/records`, both app-01 and app-02 equally
    - Postgres auth failure.
- **404 (10)** - `/missing` path, scattered through the whole window, unrelated to any
  incident (client requesting a route that doesn't exist).

## 5. Latency: median and p95

Computed over `request_time` (seconds) from access.log using linear-interpolation percentile
method:

- **Median: 0.054s**
- **p95: 2.001s**

The p95 is dominated by the Redis-timeout incident, where every affected request took almost
exactly 2.025s (matching the app's 2-second Redis connect timeout).

## 6. Retried requests

`nginx.conf` sets `proxy_next_upstream off;` - NGINX is configured to never retry a failed
request against the other upstream. Confirmed no retries occurred: the 5 duplicate
`request_id` lines found are exact duplicate log entries (identical timestamp/status/
duration), not a second attempt with a different outcome. **0 requests were retried
upstream; 0 succeeded after retrying**, by design.

## 7. Incident timeline (from access + error + application logs)

| Time (UTC) | Incident | Evidence | Requests | Client status |
|---|---|---|---|---|
| 11:05:02-11:09:57 | app-02 unreachable | error.log: `Connection refused` to `172.23.0.12:8080`; access.log: 502/504 from same upstream; no matching application.log entries (request never reached the app) | 59 | 502/504 |
| 11:12:09-11:15:52 | Redis timeout | application.log: `dependency_error`/`TimeoutError`, dependency=redis, ~2025ms duration; access.log: matching 503 with request_time≈2.025s | 31 | 503 |
| 11:20:07-11:21:45 | Postgres invalid password | application.log: `dependency_error`/`InvalidPassword`, dependency=postgres, ~41ms duration; access.log: matching 503 with request_time≈0.041s | 16 | 503 |

## 8. Correlated examples

Successful request (lab-000002): access.log shows status 200 on `/health` via upstream
172.23.0.12:8080 at 11:00:02.532Z; application.log shows the matching INFO/http_request line
for instance app-02, same timestamp, same status, duration 32ms.

Failed request (lab-000292, Redis timeout incident): access.log shows status 503 on `/ready`
via upstream 172.23.0.12:8080 at 11:12:09.525Z, request_time 2.025s; application.log shows
two matching lines with the same request_id - an ERROR/dependency_error (dependency=redis,
error_type=TimeoutError) and a WARN/http_request line with status 503, duration 2025ms.

## 9. Proxy/connectivity errors vs dependency/application errors

- **Proxy/connectivity (Incident 1):** logged only in error.log (`Connection refused`) and
  access.log (502/504). No corresponding application.log line exists for any of these
  request_ids - proof the request never reached the Flask process; NGINX itself failed to
  open a TCP connection to app-02.
- **Dependency/application errors (Incidents 2 & 3):** every failing request_id has a
  matching application.log ERROR/dependency_error line plus a WARN/http_request line with
  the same status - proof the request did reach the app, which then failed while calling
  Redis or Postgres and returned a controlled 503.

## 10. What the logs don't prove / what to check next in a live environment

The logs prove symptoms and timing, not root cause of the underlying failures:
- They don't prove why app-02 stopped accepting connections (crash? OOM? manual stop?) -
  would need `docker inspect`/`docker logs --since` on app-02 or an orchestrator event
  history from that time.
- They don't prove why Redis or Postgres briefly became unreachable/misconfigured - would
  need Redis/Postgres server-side logs and network metrics from that window, not just the
  client-side symptoms.
- They are historical (2026-08-20) and synthetic - they say nothing about the current live
  environment's health; that must be verified independently (see validate.py).
- They don't capture resource usage (CPU/memory) during the incidents, which would help
  distinguish "Redis was overloaded" from "network partition."
