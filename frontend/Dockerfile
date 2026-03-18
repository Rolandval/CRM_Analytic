# ── Build ─────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --frozen-lockfile
COPY . .
RUN npm run build

# ── Serve with nginx ──────────────────────────────────────────────────────────
FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx config for SPA (all routes → index.html)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 81
CMD ["nginx", "-g", "daemon off;"]
