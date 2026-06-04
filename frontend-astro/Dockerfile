# ============================================================================
# Frontend Dockerfile for FastBlog Astro frontend (Static Export)
# Multi-stage build: Node.js build -> Nginx static serving
# Final image size: ~50MB (vs ~1.13GB with node:20-alpine)
# ============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Build static files
# ---------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency files first (better layer caching)
COPY package*.json ./

# Install all dependencies (dev + prod) for build
RUN npm ci --legacy-peer-deps

# Copy source code
COPY . .

# Build static output (output: 'static' in astro.config.mjs)
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 2: Serve with Nginx (Alpine)
# ---------------------------------------------------------------------------
FROM nginx:1-alpine AS production

# Install curl for healthcheck (wget from BusyBox can be unreliable in some Alpine versions)
RUN apk add --no-cache curl

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config for static file serving
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built static files from builder stage
# Astro 'static' output goes to dist/
COPY --from=builder /app/dist /usr/share/nginx/html

# Add non-root user for security
RUN chown -R nginx:nginx /usr/share/nginx/html \
    && chown -R nginx:nginx /var/cache/nginx \
    && chown -R nginx:nginx /var/log/nginx \
    && touch /var/run/nginx.pid \
    && chown -R nginx:nginx /var/run/nginx.pid

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:80/ > /dev/null || exit 1

CMD ["nginx", "-g", "daemon off;"]
