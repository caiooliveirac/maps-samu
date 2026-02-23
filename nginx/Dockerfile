# ── Stage 1: Build Frontend ──
FROM node:20-alpine AS frontend-build

ARG VITE_API_URL=/api
ARG VITE_BASE=/
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_BASE=$VITE_BASE

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --prefer-offline
COPY frontend/ .
RUN npm run build

# ── Stage 2: Nginx ──
FROM nginx:1.25-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=frontend-build /app/dist /usr/share/nginx/html

EXPOSE 80
