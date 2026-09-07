<img src="assets/barq-logo.svg" alt="BARQ Systems" width="180">

# BARQ DevOps Internship Task — Completed Submission

Repository: https://github.com/kholodtawfeek/Barq-Devops-Task

This repository contains a fixed, tested and documented version of the BARQ Systems
DevOps assessment environment: two Flask instances behind NGINX, with real PostgreSQL
and Redis dependencies.

## What was broken and fixed

See `troubleshooting.md` for the full investigation journal (10 findings, symptoms,
root causes and retest evidence) and `log_analysis.md` for the historical log analysis.
Summary of fixes: healthcheck endpoint mismatch, PostgreSQL/Redis port and password
mismatches, duplicate INSTANCE_ID, NGINX upstream/published port mismatches, PostgreSQL
volume misconfiguration, a baked-in secret and a root-user container. Full reasoning and
trade-offs for each fix are in `decisions.md`.

## Before you start

- Linux or WSL2, Python 3.12+, Git and Docker with Compose.
- Docker Desktop must be running with WSL integration enabled for your distro.
- Container names used: `app-01`, `app-02`, `nginx`, `postgres`, `redis`.
- Public port: `8080` (default; changed live to `8090` during the video demonstration).

## Setup

```bash
git clone https://github.com/kholodtawfeek/Barq-Devops-Task.git
cd Barq-Devops-Task
cp .env.example .env
```

## Build and start

```bash
docker compose -p barq-assessment up --build -d
docker compose -p barq-assessment ps -a
```

Wait until all five containers show `healthy` (or `Up` for nginx, which has no
healthcheck of its own).

## Stop / restart

```bash
docker compose -p barq-assessment down      # stops and removes containers, keeps the named volume
docker compose -p barq-assessment up -d     # starts again, PostgreSQL data persists
```

## Test the endpoints

```bash
curl -i http://127.0.0.1:8080/health
curl -i http://127.0.0.1:8080/ready
curl -i http://127.0.0.1:8080/instance
curl -H 'Content-Type: application/json' -d '{"title":"Example record"}' http://127.0.0.1:8080/records
curl http://127.0.0.1:8080/records
curl http://127.0.0.1:8080/counter
```

## Run full validation

```bash
python3 validate.py
```

Runs 17 bounded checks: public access, all endpoints, both backend identities, PostgreSQL/Redis
readiness, prohibited host ports (5432/6379 must NOT be reachable), backend network isolation,
and container health. Exits non-zero if any check fails.

## Run the failure/recovery test

```bash
python3 failure_test.py
```

Stops `app-01`, proves the site stays partially available through `app-02` (NGINX has
`proxy_next_upstream off`, so requests routed to the stopped backend fail while requests
routed to the healthy one succeed — see `decisions.md` item 5 and `security_review.md` item 2
for the trade-off), then restarts `app-01` and proves it serves traffic again.

## Backup and restore (PostgreSQL)

```bash
./backup.sh            # dumps barq_tasks to ./backups/barq_tasks_<timestamp>.sql, keeps last 5
./restore.sh            # restores the most recent backup (or pass a specific file as $1)
```

Proven persistence test (also documented in `decisions.md` item 6):

```bash
curl -H 'Content-Type: application/json' -d '{"title":"Persistence proof"}' http://127.0.0.1:8080/records
./backup.sh
docker compose -p barq-assessment down
docker compose -p barq-assessment up --build -d
curl http://127.0.0.1:8080/records   # the record is still present because postgres-data is a named volume
```

## Continuous integration

`.github/workflows/ci.yml` runs on every push and pull request: checks out the repo,
validates `docker-compose.yml` syntax, builds the images, starts the stack, waits (bounded)
for `/ready`, then runs `validate.py`. The job fails if validation fails. See the Actions tab
of the repository for run history.

## Cleanup

```bash
docker compose -p barq-assessment down       # normal stop, keeps the postgres-data volume
docker compose -p barq-assessment down -v    # full cleanup INCLUDING the named volume — this deletes all PostgreSQL data
```

Avoid global `docker system prune` commands; they can affect containers/images unrelated to
this project.

## Documentation index

- `troubleshooting.md` — investigation journal (symptoms, hypotheses, root causes, retests).
- `log_analysis.md` — full answers to the 10 log-analysis template questions.
- `decisions.md` — 7 documented decisions, assumptions, alternatives and trade-offs.
- `security_review.md` — 10 concrete security risks/improvements, separated from what is
  already implemented.
- `AI_USAGE.md` — disclosure of AI-assisted work and how it was verified.
- `architecture.png` — request flow, ports, networks, storage and health-check relationships.
- `docs/EVIDENCE_INDEX.md` — maps each requirement to its file/output, commit and video timestamp.
