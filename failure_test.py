#!/usr/bin/env python3
"""Stop one backend, prove the site stays available through NGINX,
restore it, and prove it recovers. Exits non-zero on failure."""
import json
import subprocess
import sys
import time
import urllib.request
import urllib.error

PROJECT = "barq-assessment"
BASE_URL = "http://127.0.0.1:8080"
TARGET = "app-01"
TIMEOUT = 5
REQUESTS_DURING_FAILURE = 10
MAX_WAIT_RECOVERY = 30

results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))


def http_get(path):
    url = BASE_URL + path
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, json.loads(resp.read()), dict(resp.headers)
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read())
        except Exception:
            body = {}
        return e.code, body, dict(e.headers)


def docker(*args):
    return subprocess.run(
        ["docker", "compose", "-p", PROJECT, *args],
        capture_output=True, text=True, check=True,
    )


def container_state(name):
    out = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Status}}", name],
        capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


def main():
    # 0. Baseline: confirm both backends serve traffic before the test
    seen_before = set()
    for _ in range(20):
        try:
            _, _, headers = http_get("/instance")
            seen_before.add(headers.get("X-Instance-ID"))
        except Exception:
            pass
        if {"app-01", "app-02"} <= seen_before:
            break
        time.sleep(0.2)
    record("baseline_both_backends_serving", {"app-01", "app-02"} <= seen_before,
           f"seen={seen_before}")

    # 1. Stop the target backend
    print(f"\nStopping {TARGET} ...")
    docker("stop", TARGET)
    time.sleep(2)
    state = container_state(TARGET)
    record("target_backend_stopped", state == "exited", f"state={state}")

    # 2. Traffic and errors during failure: site must stay available via the other backend
    ok_count, error_count, seen_during = 0, 0, set()
    for _ in range(REQUESTS_DURING_FAILURE):
        try:
            status, _, headers = http_get("/instance")
            if status == 200:
                ok_count += 1
                seen_during.add(headers.get("X-Instance-ID"))
            else:
                error_count += 1
        except Exception:
            error_count += 1
        time.sleep(0.3)
    record("site_stays_available_during_failure", ok_count > 0,
           f"ok={ok_count} errors={error_count} out of {REQUESTS_DURING_FAILURE} requests")
    record("only_surviving_backend_served_traffic", seen_during == {"app-02"} if TARGET == "app-01"
           else seen_during == {"app-01"}, f"seen_during_failure={seen_during}")

    # Also confirm /health and /ready still succeed through NGINX during the outage
    try:
        status, _, _ = http_get("/health")
        record("health_ok_during_failure", status == 200, f"status={status}")
    except Exception as exc:
        record("health_ok_during_failure", False, str(exc))

    # 3. Restore the backend
    print(f"\nRestarting {TARGET} ...")
    docker("start", TARGET)

    # 4. Wait (bounded) for it to become healthy again
    deadline = time.time() + MAX_WAIT_RECOVERY
    recovered = False
    while time.time() < deadline:
        state = container_state(TARGET)
        if state == "running":
            out = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Health.Status}}", TARGET],
                capture_output=True, text=True,
            )
            if out.stdout.strip() == "healthy":
                recovered = True
                break
        time.sleep(1)
    record("target_backend_recovered", recovered, f"waited up to {MAX_WAIT_RECOVERY}s")

    # 5. Prove the recovered backend actually serves requests again
    seen_after = set()
    for _ in range(30):
        try:
            _, _, headers = http_get("/instance")
            seen_after.add(headers.get("X-Instance-ID"))
        except Exception:
            pass
        if TARGET in seen_after:
            break
        time.sleep(0.3)
    record("recovered_backend_serving_again", TARGET in seen_after, f"seen_after={seen_after}")

    print()
    failed = [r for r in results if not r[1]]
    print(f"Summary: {len(results) - len(failed)}/{len(results)} checks passed")
    if failed:
        print("Failed checks:")
        for name, _, detail in failed:
            print(f"  - {name}: {detail}")
        sys.exit(1)
    print("All checks passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
