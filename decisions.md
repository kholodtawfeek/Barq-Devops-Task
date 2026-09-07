# Decisions

## 1. Fixed healthcheck endpoint mismatch (/healthz -> /health)
The Docker healthcheck targeted `/healthz`, which does not exist in the app contract.
Assumption: the intended liveness endpoint is `/health` per assessment/APPLICATION.md.
Alternative considered: add a `/healthz` alias route in the app instead. Rejected because
the contract explicitly defines `/health` as the canonical endpoint; adding an alias would
hide the original bug rather than fix it.
Trade-off: none significant; this was a straightforward one-line fix.

## 2. Corrected PostgreSQL/Redis ports and password in config/app.env
The app was configured to reach postgres:5433 and redis:6380, while both services actually
listen on their default ports (5432/6379) inside the Docker network. The Postgres password
in app.env also did not match POSTGRES_PASSWORD in docker-compose.yml.
Assumption: the compose file's values are authoritative (source of truth for actual service
config); app.env was the file with the drift.
Alternative considered: change docker-compose.yml's ports/password to match app.env instead.
Rejected because docker-compose.yml directly controls what the containers actually expose,
so it is the more reliable reference point.
Limitation: this fix relies on both files being kept in sync manually; in production this
would be better handled by generating both from one source (e.g. a single secrets manager).

## 3. Removed the copied secret file from the Docker image, kept env_file injection only
The Dockerfile copied config/app.env directly into the image (`/srv/app.env`), while Compose
already injects it at runtime via `env_file`. This baked real credentials into every image
layer.
Decision: removed the `COPY config/app.env` line entirely; the app already reads its config
from environment variables at runtime.
Alternative considered: keep the copy but add config/app.env to .dockerignore. Rejected
because the app never needed the file inside the image in the first place — deleting the
line is simpler and leaves no secret material in the image history at all.
Trade-off: none; this is a strict improvement with no functional downside.

## 4. Switched the app container back to a non-root user
The Dockerfile created a dedicated `app` user (uid 10001) but then explicitly set `USER root`,
so the process ran as root despite the setup work already being done.
Decision: changed the final `USER` directive to `USER app`.
Assumption: the app process does not need root privileges (it only binds to a non-privileged
port >1024 and talks to Postgres/Redis over the network), which was confirmed by testing after
the change — the app still starts and serves requests normally as user `app`.
Trade-off: none observed; this is a security improvement with no loss of functionality.

## 5. Kept `proxy_next_upstream off` in nginx.conf despite the availability trade-off
NGINX is configured with `proxy_next_upstream off`, meaning a request routed to a backend that
is down fails outright instead of being retried against the other backend.
Assumption: this was the setting the starter already shipped with, and the task only asked to
fix the upstream port mismatch (8081 -> 8080), not to change failover behavior.
Alternative considered: turn failover on (`proxy_next_upstream error timeout;`) so a stopped
backend would not cause any client-visible failures at all.
Trade-off accepted: keeping it `off` means `failure_test.py` correctly shows partial failures
(~50% of requests) while one backend is down, which is arguably more honest/observable
behavior for this assessment, but it is a real single point of failure — documented in
security_review.md as a risk to fix for production (add active/passive upstream health checks
and re-enable retries).

## 6. Named PostgreSQL volume mounted at the correct data directory
The named volume `postgres-data` was originally mounted at `/var/lib/postgresql/backup`, while
the actual PostgreSQL data directory (`/var/lib/postgresql/data`) was set to `tmpfs` — meaning
all data was wiped on every container restart, and the named volume protected nothing.
Decision: mounted `postgres-data` directly at `/var/lib/postgresql/data` and removed the
conflicting `tmpfs` entry.
Verified by proof: created a record, ran `docker compose down` + `up --build`, and confirmed
the record survived (see README.md / troubleshooting.md for the exact commands and output).

## 7. Kept container-to-container communication on service names only, no published dependency ports
Postgres and Redis originally published host ports (`127.0.0.1:15432:5432`, `127.0.0.1:16379:6379`)
in addition to being reachable via the internal `backend` network.
Decision: removed both host-published ports entirely, since the task requires only NGINX to be
reachable from the host, and app-to-dependency traffic already uses service names
(`postgres`, `redis`) over the internal Docker network.
Verified by proof: `validate.py`'s `postgres_port_hidden` and `redis_port_hidden` checks both
pass, confirming neither port is reachable from the host machine.
