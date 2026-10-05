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

Use Node.js 24 LTS and pnpm 12.3.4 (pinned in `package.json`).

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

Production Kubernetes pins a short SHA tag through an infra image update PR.
Pull request previews use the full SHA of the last successfully published image,
recorded as `publishedSha` in `infra/previews/tanstack-demo/<number>.json`.

After publishing to GHCR, the `publish-preview` job records the image in infra
using `INFRA_APP_CLIENT_ID` and `INFRA_APP_PRIVATE_KEY`. It skips closed PRs and
superseded builds. Failed builds preserve the previous image; a new PR gets a
preview only after its first successful publication. Argo CD removes the preview
when the PR closes.

Pull request builds then wait for `/health` to return the expected
`x-preview-image-tag` header and update the PR with the preview URL. Kubernetes
sets `APP_IMAGE_TAG` from the deployed image tag.

## Dependency release age

pnpm requires every dependency, including transitive dependencies, to be at least
seven days old (`minimumReleaseAge: 10080` minutes). There are no package age
exceptions. Renovate waits seven days plus a one-hour buffer for npm releases
and uses strict internal checks to defer branches and PRs until the age check
passes. The buffer accommodates companion packages published slightly later.

Existing dependency PRs may still contain younger releases or transitive
dependencies. They must pass pnpm's policy before an image can be published;
waiting alone does not rerun failed CI.

## Deployment URLs

```text
Production: https://tanstack-demo.echoja.com
Preview:    https://tanstack-demo-pr-<number>.echoja.com
Health:     /health
```
