# =============================================================================
# FRONTEND DOCKERFILE - Multi-stage build for dev and production
# =============================================================================
#
# Stages:
#   - base: Common dependencies
#   - development: Hot reload with next dev
#   - builder: Build production assets
#   - production: Optimized Next.js standalone
#
# Usage:
#   Dev:  docker build --target development -t champion-frontend:dev .
#   Prod: docker build --target production -t champion-frontend:prod .
# =============================================================================

# =============================================================================
# BASE STAGE - Common dependencies
# =============================================================================
FROM node:20-alpine AS base

WORKDIR /app

# Install dependencies for native modules
RUN apk add --no-cache libc6-compat

# =============================================================================
# DEVELOPMENT STAGE - Hot reload with Next.js dev server
# =============================================================================
FROM base AS development

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source (will be overridden by volume mount in docker-compose)
COPY . .

# Expose dev server port
EXPOSE 3000

# Development environment
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1

# Start dev server with hot reload
CMD ["npm", "run", "dev"]

# =============================================================================
# BUILDER STAGE - Build production assets
# =============================================================================
FROM base AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Build args for environment
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Copy source and build
COPY . .

# Disable telemetry during build
ENV NEXT_TELEMETRY_DISABLED=1

# Build the application
RUN npm run build

# =============================================================================
# PRODUCTION STAGE - Optimized Next.js standalone
# =============================================================================
FROM base AS production

WORKDIR /app

# Production environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy built assets from builder
COPY --from=builder /app/public ./public

# Set correct permissions for prerender cache
RUN mkdir .next && chown nextjs:nodejs .next

# Copy standalone build
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user
USER nextjs

# Expose production port
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Start production server
CMD ["node", "server.js"]
