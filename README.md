# network-diag-tool

**Live demo:** admin UI https://admin.albertycliu.xyz, user UI https://diag.albertycliu.xyz (no login on purpose, for the demo)

A small web tool for diagnosing whether a set of sites and APIs is reachable from a user's browser.

- An admin creates a **session** (a list of target URLs) and shares its link.
- The user opens the link, the browser checks each URL and reports status codes and errors, and can upload a HAR capture.
- The admin lists sessions, reports and HAR files.

## Architecture

| Part | Tech | Notes |
| --- | --- | --- |
| admin-frontend | Vue 3 + Quasar, nginx | serves the admin UI, proxies `/api` to admin-backend |
| admin-backend | Flask + SQLAlchemy, gunicorn | MariaDB |
| user-frontend | Vue 3 + Quasar, nginx | the page a user opens, proxies `/api` to user-backend |
| user-backend | Flask + SQLAlchemy, gunicorn | SQLite, forwards reports to admin-backend |
| mariadb | MariaDB 11.1 | admin data |

The browser only talks to one host per UI on 80/443. The frontends call relative `/api/...` paths and nginx proxies them to the backend, so no backend ports are exposed.

## Run locally

```
cp .env.example .env      # set MYSQL_ROOT_PASSWORD
docker compose up --build
```

Admin UI: http://localhost:8080, user UI: http://localhost:8081.

## CI/CD

Pushing to `main` runs GitHub Actions (`.github/workflows/ci.yml`):

1. test: import check for both backends, production build for both frontends
2. build: build and push 4 images to GHCR (`ghcr.io/albertycl/network-diag-tool-<part>`), tagged with the commit SHA
3. update-gitops: commit the new image tags to [`Albertycl/gitops-apps`](https://github.com/Albertycl/gitops-apps)

Argo CD on a K3s cluster watches `gitops-apps` and deploys the change.
