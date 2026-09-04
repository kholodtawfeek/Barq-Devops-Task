# Troubleshooting Journal

## Initial investigation

### Finding 1 - Application health check fails

Symptom:
Both app containers remain in health: starting.

Evidence:
The application logs show GET /healthz returning HTTP 404.

Hypothesis:
The Docker healthcheck targets an endpoint that does not exist.

Command:
docker compose -p barq-assessment ps -a
docker compose -p barq-assessment logs --no-color

Result:
PostgreSQL and Redis are healthy, while both application healthchecks repeatedly receive 404 from /healthz.

Root cause:
docker-compose.yml checks /healthz, while the application contract defines /health as the liveness endpoint.

Status:
Confirmed; fix pending.

### Finding 2 - PostgreSQL port mismatch

Symptom:
Application configuration points to postgres:5433.

Evidence:
config/app.env uses postgres:5433 while PostgreSQL listens on port 5432 inside the container.

Root cause:
Incorrect container-to-container PostgreSQL port.

Status:
Confirmed; fix pending.

### Finding 3 - Redis port mismatch

Symptom:
Application configuration points to redis:6380.

Evidence:
config/app.env uses redis:6380 while Redis listens on 6379.

Root cause:
Incorrect container-to-container Redis port.

Status:
Confirmed; fix pending.

### Finding 4 - PostgreSQL password mismatch

Symptom:
The password configured for the application differs from the PostgreSQL service password.

Evidence:
config/app.env ends with K8d while docker-compose.yml ends with K8c.

Root cause:
Inconsistent credentials between application and database configuration.

Status:
Confirmed; fix pending.

### Finding 5 - Duplicate application identity

Symptom:
app-02 reports instance_id=app-01.

Root cause:
docker-compose.yml assigns INSTANCE_ID=app-01 to both app instances.

Status:
Confirmed; fix pending.

### Finding 6 - NGINX upstream port mismatch

Symptom:
NGINX configuration points app-01 to port 8081.

Evidence:
Both Flask instances are configured to listen on port 8080.

Root cause:
Incorrect NGINX upstream port for app-01.

Status:
Confirmed; fix pending.

### Finding 7 - NGINX published port mismatch

Symptom:
Compose publishes host port 8080 to container port 81.

Evidence:
NGINX configuration listens on port 80.

Root cause:
Published container port does not match NGINX listen port.

Status:
Confirmed; fix pending.

### Finding 8 - PostgreSQL persistence configuration

Symptom:
The named volume is mounted at /var/lib/postgresql/backup while the PostgreSQL data directory is /var/lib/postgresql/data, which is configured as tmpfs.

Root cause:
The named volume is not protecting the actual PostgreSQL data directory.

Status:
Confirmed; fix pending.

### Finding 9 - Application runs as root

Evidence:
Dockerfile creates an app user but switches back to USER root.

Root cause:
The application container does not use the non-root user that was created.

Status:
Confirmed; fix pending.

### Finding 10 - Secrets/config copied into image

Evidence:
Dockerfile copies config/app.env into /srv/app.env while Compose already injects it through env_file.

Root cause:
Sensitive runtime configuration is unnecessarily included in the image.

Status:
Confirmed; fix pending.

