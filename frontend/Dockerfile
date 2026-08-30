# syntax=docker/dockerfile:1
# ---------- deps + build ----------
FROM node:20-alpine AS builder
WORKDIR /app

COPY frontend/package.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ---------- runtime ----------
FROM node:20-alpine
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

RUN addgroup -S -g 1001 app && adduser -S -u 1001 -G app app

ENV NODE_ENV=production

COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/next.config.js ./

USER app
EXPOSE 3000

CMD ["npm", "start"]