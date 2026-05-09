# tanstack-demo

TanStack Start demo app for `tanstack-demo.echoja.com`.

## Stack

- TanStack Start, Router, Query, Form, Devtools
- Better Auth with email/password
- Drizzle ORM with PostgreSQL
- Sentry instrumentation hooks
- Tailwind CSS v4
- Docker image published to GitHub Container Registry

## Local Development

```bash
pnpm install
cp .env.example .env.local
pnpm dev
```

The dev server listens on `http://localhost:37291`.

## Environment

```text
DATABASE_URL=postgres://tanstack_demo:tanstack_demo@localhost:5432/tanstack_demo
BETTER_AUTH_URL=http://localhost:37291
BETTER_AUTH_SECRET=<random-secret>
VITE_SENTRY_DSN=
VITE_SENTRY_ORG=
VITE_SENTRY_PROJECT=
SENTRY_AUTH_TOKEN=
```

For production, `BETTER_AUTH_URL` is `https://tanstack-demo.echoja.com`.

## Docker

```bash
docker build -t ghcr.io/echoja/tanstack-demo:local .
docker compose up -d --build
```

The container runs migrations on boot and connects to PostgreSQL through `DATABASE_URL`.

## Image Tags

GitHub Actions publishes:

```text
ghcr.io/echoja/tanstack-demo:main
ghcr.io/echoja/tanstack-demo:pr-<pull-request-number>
ghcr.io/echoja/tanstack-demo:sha-<commit-sha>
```

Production Kubernetes uses `main`. Pull request previews use `sha-<pull-request-head-sha>`.

## Deployment URLs

```text
Production: https://tanstack-demo.echoja.com
Preview:    https://pr-<number>.tanstack-demo.echoja.com
Health:     /health
```
