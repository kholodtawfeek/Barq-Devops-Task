# Security review

## Implemented fixes (already in this solution)

1. **Secrets removed from the image.** `config/app.env` is no longer copied into the Docker
   image; it is only injected at runtime via Compose's `env_file`. The image itself contains
   no credentials.
2. **Non-root container user.** The app Dockerfile creates and runs as a dedicated `app` user
   (uid 10001) instead of root, limiting the blast radius of a container compromise.
3. **No dependency ports published to the host.** PostgreSQL and Redis are only reachable via
   the internal `backend` Docker network (`internal: true`), not from the host machine or
   the public internet. Verified by `validate.py`.
4. **Only NGINX exposed publicly.** A single host port (8080) is published; app containers
   have no published ports at all, reducing the public attack surface to one component.
5. **`.env` kept out of version control.** `.env` (containing the real `PUBLIC_PORT` and any
   local overrides) is gitignored; only `.env.example` (no real secrets) is committed.

## Concrete risks / improvements for production

1. **Plaintext secrets in `config/app.env` and `docker-compose.yml`.** The PostgreSQL password
   is stored as plain text in both files. Production improvement: use Docker secrets, a vault
   (HashiCorp Vault, AWS Secrets Manager) or at minimum environment injection from a CI/CD
   secrets store, never committed to the repo at all.
2. **No automatic upstream failover in NGINX (`proxy_next_upstream off`).** As shown by
   `failure_test.py`, roughly half of requests fail outright while one backend is down, since
   NGINX will not retry against the healthy instance. Fix: enable
   `proxy_next_upstream error timeout;` combined with passive health checks, or use an
   NGINX Plus / Envoy-style active health check so failing backends are removed from rotation
   automatically.
3. **No resource limits set on any container.** None of the services in docker-compose.yml
   define `deploy.resources.limits` (CPU/memory). A runaway process in any single container
   could starve the host. Fix: add explicit memory/CPU limits per service, sized from observed
   load.
4. **No monitoring/alerting stack.** Health is only checked reactively (via `/ready` and
   Docker healthchecks); there is no Prometheus/Grafana or equivalent to alert on elevated
   error rates or dependency failures before users notice. Fix: export metrics from the Flask
   app and NGINX, scrape with Prometheus, alert on error-rate and latency thresholds.
5. **No TLS termination.** NGINX currently serves plain HTTP on port 8080/8090. In production
   this must sit behind TLS (either terminated at NGINX with a real certificate, or behind a
   cloud load balancer/ingress that terminates TLS).
6. **Postgres backups are manual and local-disk only.** `backup.sh` writes `.sql` dumps to a
   local `./backups` folder with no off-host replication or automated schedule. Fix: run
   backups on a schedule (cron/CI), and ship them to durable off-host storage (S3 or similar)
   with retention and restore-testing automation, not just a manual script.
7. **No structured/centralized logging.** Application and NGINX logs are only visible via
   `docker compose logs` on the host running the containers. Fix: ship logs to a centralized
   system (ELK/Loki) so incidents can be investigated after containers are recreated or
   removed, and so historical correlation (like the one done in log_analysis.md) doesn't
   depend on log files still being present on disk.
8. **Single instance of PostgreSQL and Redis (no replication).** Both dependency services are
   single points of failure — if the `postgres` or `redis` container/host fails, the entire
   system becomes unavailable regardless of how many app instances are running. Fix: use a
   managed, replicated database service (e.g. RDS Multi-AZ) and a Redis cluster/replica setup
   in production.
9. **Restart policy is `restart: "no"` on app services.** If an app container crashes, Compose
   will not restart it automatically; only the Docker healthcheck marks it unhealthy without
   recovering it. Fix: use `restart: unless-stopped` (or an orchestrator like Kubernetes with
   proper liveness/readiness probes) so crashed containers self-heal.
10. **Pinned image digests but no active vulnerability scanning.** Images are pinned to a
    specific `sha256` digest (good for reproducibility) but nothing in the pipeline scans them
    for known CVEs. Fix: add a Trivy/Grype scan step to CI (see optional extra-credit scan) and
    fail the build on high-severity findings.

## Persistence and logging risks (explicitly separated from what's implemented)

- **Implemented:** the PostgreSQL named volume (`postgres-data`) correctly persists data across
  container recreation — proven by creating a record, running `docker compose down && up`, and
  confirming the record survives.
- **Not implemented / production gap:** there is no automated backup schedule, no
  backup-integrity verification job, and no log retention/rotation policy beyond what Docker's
  default logging driver provides. In a real production system these would need to be built
  out separately from the manual `backup.sh`/`restore.sh` scripts used here.
