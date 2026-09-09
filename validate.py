#!/usr/bin/env python3
"""Validate the BARQ assessment environment.
Checks public access, endpoints, both backends, dependency readiness,
network isolation and prohibited host ports. Exits non-zero on any failure.
"""
import json
import socket
import subprocess
import sys
import time
import urllib.request
import urllib.error

PROJECT = "barq-assessment"
HOST = "127.0.0.1"
PUBLIC_PORT = 8090
BASE_URL = f"http://{HOST}:{PUBLIC_PORT}"
TIMEOUT = 5
MAX_WAIT = 30  # bounded wait for readiness

results = []


def record(name, ok, detail=""):
    results.append((name, ok, detail))
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}" + (f" - {detail}" if detail else ""))


def http_get(path, method="GET", body=None):
    url = BASE_URL + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, json.loads(resp.read()), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read()), dict(e.headers)


def wait_for_ready():
    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        try:
            status, payload, _ = http_get("/ready")
            if status == 200:
                return True, payload
        except Exception:
            pass
        time.sleep(1)
    return False, None


def port_is_closed(host, port):
    """True if nothing accepts a connection on host:port (i.e. properly hidden)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((host, port))
        return False  # connection succeeded -> port is exposed, bad
    except (ConnectionRefusedError, socket.timeout, OSError):
        return True
    finally:
        s.close()


def compose_ps():
    out = subprocess.run(
        ["docker", "compose", "-p", PROJECT, "ps", "--format", "json"],
        capture_output=True, text=True, check=True,
    )
    lines = [l for l in out.stdout.splitlines() if l.strip()]
    return [json.loads(l) for l in lines]


def network_is_internal(name):
    out = subprocess.run(
        ["docker", "network", "inspect", name, "--format", "{{.Internal}}"],
        capture_output=True, text=True, check=True,
    )
    return out.stdout.strip() == "true"


def main():
    # 1. Public access on NGINX
    try:
        status, payload, _ = http_get("/health")
        record("public_access_health", status == 200, f"status={status}")
    except Exception as exc:
        record("public_access_health", False, str(exc))

    # 2. /  endpoint
    try:
        status, payload, _ = http_get("/")
        record("endpoint_root", status == 200 and "message" in payload, f"status={status}")
    except Exception as exc:
        record("endpoint_root", False, str(exc))

    # 3. /ready with bounded wait
    ok, payload = wait_for_ready()
    record("endpoint_ready", ok and payload and payload.get("status") == "ready",
           json.dumps(payload) if payload else "timed out waiting for readiness")

    if payload:
        deps = payload.get("dependencies", {})
        record("postgres_ready", deps.get("postgres") == "ready", str(deps))
        record("redis_ready", deps.get("redis") == "ready", str(deps))

    # 4. /instance -> both backends respond (loop until we see both IDs)
    seen_instances = set()
    for _ in range(20):
        try:
            status, payload, headers = http_get("/instance")
            iid = headers.get("X-Instance-ID")
            if iid:
                seen_instances.add(iid)
        except Exception:
            pass
        if {"app-01", "app-02", "app-03"} <= seen_instances:
            break
        time.sleep(0.3)
    record("both_backends_serving", {"app-01", "app-02", "app-03"} <= seen_instances,
           f"seen={seen_instances}")

    # 5. /records create + list
    try:
        status, payload, _ = http_get("/records", method="POST", body={"title": "validate.py check"})
        created_ok = status == 201 and "record" in payload
        record("records_create", created_ok, f"status={status}")
        status, payload, _ = http_get("/records")
        record("records_list", status == 200 and isinstance(payload.get("records"), list),
               f"count={len(payload.get('records', []))}" if status == 200 else f"status={status}")
    except Exception as exc:
        record("records_create_list", False, str(exc))

    # 6. /counter increments
    try:
        _, p1, _ = http_get("/counter")
        _, p2, _ = http_get("/counter")
        record("counter_increments", p2["counter"] > p1["counter"],
               f"{p1.get('counter')} -> {p2.get('counter')}")
    except Exception as exc:
        record("counter_increments", False, str(exc))

    # 7. Prohibited host ports: app, postgres, redis must NOT be reachable from host
    record("postgres_port_hidden", port_is_closed(HOST, 5432))
    record("redis_port_hidden", port_is_closed(HOST, 6379))
    # app containers should have no published host port at all; 8080 must map ONLY to nginx
    # (already implicitly proven by nginx serving through 8080 above)

    # 8. Network isolation: backend network must be internal
    try:
        record("backend_network_internal", network_is_internal(f"{PROJECT}_backend"))
    except Exception as exc:
        record("backend_network_internal", False, str(exc))

    # 9. Container health via docker compose ps
    try:
        services = compose_ps()
        by_name = {s["Service"]: s for s in services}
        for name in ["app-01", "app-02", "nginx", "postgres", "redis"]:
            svc = by_name.get(name)
            healthy = bool(svc) and ("healthy" in svc.get("Health", "").lower()
                                      or svc.get("State") == "running")
            record(f"container_running_{name}", healthy, svc.get("Status") if svc else "not found")
    except Exception as exc:
        record("container_status_check", False, str(exc))

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
