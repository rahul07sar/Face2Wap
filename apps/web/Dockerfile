# ============================================================================
# Face2Wap
# ----------------------------------------------------------------------------
# File:        Dockerfile
# Module:      Web Application
# Description:
#
# Builds and runs the Face2Wap Next.js frontend application using a
# production-oriented multi-stage Docker build.
#
# ============================================================================

# ============================================================================
# Dependencies
# ============================================================================

FROM node:24-alpine AS dependencies

WORKDIR /app

COPY apps/web/package.json apps/web/package-lock.json ./

RUN npm ci


# ============================================================================
# Build
# ============================================================================

FROM node:24-alpine AS builder

WORKDIR /app

COPY --from=dependencies /app/node_modules ./node_modules
COPY apps/web ./

RUN npm run build


# ============================================================================
# Runtime
# ============================================================================

FROM node:24-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/package-lock.json ./package-lock.json
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

EXPOSE 3000

CMD ["npm", "start"]