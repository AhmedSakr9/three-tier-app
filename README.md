# Three-Tier App: Nginx, Flask API, PostgreSQL

![CI](https://github.com/AhmedSakr9/three-tier-app/actions/workflows/ci.yml/badge.svg)

A hands-on lab: a three-tier application run with Docker Compose, where only
the reverse proxy is exposed and the data lives in PostgreSQL.

## Architecture

```
Browser -> nginx (:8080) -> api (Flask + gunicorn, :5000) -> db (PostgreSQL, :5432) -> volume db-data
```

| Tier | Service | Notes |
|------|---------|-------|
| Entry point | `nginx` | Reverse proxy, the only published port |
| Application | `api` | Flask + gunicorn, non-root user, retries until the DB is ready |
| Data | `db` | PostgreSQL 16, healthcheck, persistent volume |

## Design decisions

- **Only Nginx is exposed.** `api` and `db` have no published ports.
- **Secrets stay out of Git.** The password lives in `.env`, which is ignored; `.env.example` is the template.
- **Compose refuses to start without a password** (`${POSTGRES_PASSWORD:?...}`).
- **Start order and readiness:** `depends_on` with `service_healthy`, plus a retry loop in the API.
- **Pinned image versions** for reproducible builds.

## Run it

```bash
git clone https://github.com/AhmedSakr9/three-tier-app.git
cd three-tier-app
cp .env.example .env     # then set a real POSTGRES_PASSWORD
docker compose up -d --build
curl localhost:8080/api/health
curl -X POST localhost:8080/api/notes -H "Content-Type: application/json" -d '{"text":"hello"}'
curl localhost:8080/api/notes
```

## CI

GitHub Actions builds the stack, waits for the API through Nginx, writes and
reads a note end to end, and checks that the API and database ports are not exposed.

## Problems I hit

| Problem | Cause | Fix |
|---------|-------|-----|
| API exited with code 3 | DB volume had a different password than `.env` | Reset the volume; Postgres reads the password only at first init |
| Gunicorn `WORKER TIMEOUT` loop | Worker heartbeat on a slow filesystem | `--worker-tmp-dir /dev/shm` |
| Root-owned project files | Ran editors/commands with `sudo` | `chown -R`, stopped using `sudo` |

## Roadmap

- [ ] Vulnerability scan with Trivy in CI
- [ ] Push the image to GitHub Container Registry
