FROM node:22-bookworm-slim AS base
LABEL org.opencontainers.image.source="https://github.com/echoja/tanstack-demo"
LABEL org.opencontainers.image.description="TanStack Start demo for echoja.com"
ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH
RUN corepack enable
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app

FROM base AS build
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build

FROM base AS runtime
ENV NODE_ENV=production
COPY --from=build /app/package.json /app/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile --prod
COPY --from=build /app/dist ./dist
COPY --from=build /app/server-entry.mjs ./server-entry.mjs
COPY --from=build /app/drizzle ./drizzle
COPY --from=build /app/drizzle.config.ts ./drizzle.config.ts
COPY --from=build /app/src/db ./src/db
ENV PORT=37291
ENV HOST=0.0.0.0
EXPOSE 37291
CMD ["sh", "-c", "pnpm db:migrate && node --import ./dist/server/instrument.server.mjs server-entry.mjs"]
